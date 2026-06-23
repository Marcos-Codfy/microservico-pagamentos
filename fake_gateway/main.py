"""
Fake Payment Gateway - simula um gateway externo (tipo Mercado Pago).

Roda em container isolado na porta 8001. Sempre autoriza pagamentos.

Recebe o header X-Request-ID enviado pelo microserviço de pagamentos
e logga — assim conseguimos correlacionar logs dos dois serviços
quando rastreamos uma transação ponta-a-ponta.
"""
import logging
import sys
from uuid import uuid4

from fastapi import FastAPI, Header
from pydantic import BaseModel

# Logging simples (texto mesmo, sem JSON formatter — é um fake serviço).
# Em produção, esse gateway também teria structured logging,
# mas mantemos simples aqui pra focar a complexidade no app principal.
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="[fake_gateway] %(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Fake Payment Gateway",
    version="0.1.0",
)


class AutorizacaoRequest(BaseModel):
    valor: float
    metodo: str


class AutorizacaoResponse(BaseModel):
    autorizado: bool
    transacao_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/autorizar", response_model=AutorizacaoResponse)
def autorizar(
    request: AutorizacaoRequest,
    x_request_id: str | None = Header(default=None),
) -> AutorizacaoResponse:
    """
    Autoriza um pagamento (sempre aprovado, é fake).

    O parâmetro x_request_id é extraído automaticamente pelo FastAPI
    do header HTTP "X-Request-ID" (FastAPI converte hífen pra underscore).
    Se o cliente não mandou, vem None — logamos como "-".
    """
    correlation = x_request_id or "-"
    logger.info(
        f"recebido autorizar metodo={request.metodo} "
        f"valor={request.valor} x_request_id={correlation}"
    )

    return AutorizacaoResponse(
        autorizado=True,
        transacao_id=f"fake-{uuid4()}",
    )