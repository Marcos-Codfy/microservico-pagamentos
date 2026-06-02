"""
Rotas HTTP do domínio de pagamento.

Esta é a "camada externa" da aplicação (Clean Architecture).
Responsabilidades:
- Receber requisições HTTP e validar entrada (delegado ao Pydantic).
- Chamar a lógica de negócio na camada `core`.
- TRADUZIR exceções de domínio em respostas HTTP apropriadas.

O que esta camada NÃO faz:
- Não contém regras de negócio (essas vivem em `core/calculadora.py`).
- Não conhece detalhes de persistência (não importa banco de dados).
- Não calcula juros, parcelas, etc.

Princípio aplicado: Anti-Corruption Layer — isolamos o núcleo
(domínio) das bordas técnicas (HTTP, framework).
"""

from fastapi import APIRouter, HTTPException, status

from app.core.calculadora import processar_pagamento
from app.core.exceptions import PagamentoInvalidoError
from app.schemas.pagamento import PagamentoRequest, PagamentoResponse

# prefix="/pagamentos" → todas as rotas deste router começam com /pagamentos
# tags=["pagamentos"]  → agrupa as rotas na documentação Swagger
router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])

@router.post(
    "/",
    response_model=PagamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo Pagamento",
    description="Processa um pedido de pagamento aplicando regras de juros e parcelamento.",
)
def criar_pagamento(request: PagamentoRequest) -> PagamentoResponse:
    """
    Endpoint POST /pagamentos.

    Fluxo:
    1. FastAPI valida o JSON de entrada contra o schema `PagamentoRequest`
       (Pydantic). Se inválido → 422 automático.
    2. Chamamos a calculadora pura na camada `core`.
    3. Se a calculadora lançar `PagamentoInvalidoError` (regra de negócio
       violada), traduzimos para HTTP 422 com a mensagem da exceção.
    4. Se tudo der certo, devolvemos `PagamentoResponse` com status 201.
    """
    try:
        return processar_pagamento(request)
    except PagamentoInvalidoError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erro),
        )