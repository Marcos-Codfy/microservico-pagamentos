"""
Middleware HTTP que gera/propaga Correlation ID (X-Request-ID) em cada request.

Fluxo:
1. Antes do router rodar, este middleware é chamado.
2. Se o cliente mandou X-Request-ID no header, usamos esse valor.
   Se não mandou, geramos um UUID novo.
3. Setamos o valor no contextvars — fica disponível em TODA função
   chamada durante este request, sem precisar passar como argumento.
4. Depois que o router responde:
    - logamos "request.completo" (o request_id entra automaticamente via Filter)
    - devolvemos o X-Request-ID no header da resposta
    - resetamos o contextvars
"""
import contextvars
import logging
import uuid

from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response


# Nome canônico do header que carrega o correlation ID.
# Convenção de mercado: X-Request-ID (também aparece como X-Correlation-ID).
HEADER_NAME = "X-Request-ID"


# ContextVar global do processo. Cada request tem seu próprio valor isolado
# (graças à integração contextvars + async). Default "-" pra logs fora de
# request (ex.: log do startup).
request_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


logger = logging.getLogger(__name__)


async def correlation_id_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """
    Lê/gera o correlation ID, propaga via contextvars e loga o request.
    """
    # 1. Pega do header de entrada ou gera novo.
    incoming_id = request.headers.get(HEADER_NAME)
    request_id = incoming_id if incoming_id else str(uuid.uuid4())

    # 2. Seta no contextvar — token serve pra resetar depois.
    token = request_id_ctx_var.set(request_id)

    try:
        # 3. Deixa o pipeline seguir (router → handler → response).
        response = await call_next(request)

        # 4. Devolve o ID no header da resposta (cliente vê e pode citar
        # em suporte/log/relatório de erro).
        response.headers[HEADER_NAME] = request_id

        # 5. Log estruturado do request inteiro. O request_id entra
        # AUTOMATICAMENTE via Filter — não passamos no extra.
        logger.info(
            "request.completo",
            extra={
                "metodo": request.method,
                "rota": request.url.path,
                "status_code": response.status_code,
            },
        )

        return response
    finally:
        # 6. Limpa o contextvars — devolve pro estado anterior ao set.
        # SEMPRE em finally: se o router explodir, ainda limpamos.
        request_id_ctx_var.reset(token)