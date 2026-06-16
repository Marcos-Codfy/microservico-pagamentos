"""
Rotas HTTP do domínio de pagamento.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.calculadora import processar_pagamento
from app.core.exceptions import PagamentoInvalidoError
from app.db.database import get_db
from app.db.repositorio import buscar_pagamento_por_id, salvar_pagamento
from app.schemas.pagamento import PagamentoRequest, PagamentoResponse

router = APIRouter(prefix="/pagamentos", tags=["pagamentos"])


@router.post(
    "/",
    response_model=PagamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo Pagamento",
    description="Processa um pedido de pagamento, persiste no banco e devolve o resultado.",
)
def criar_pagamento(
    request: PagamentoRequest,
    db: Session = Depends(get_db),
) -> PagamentoResponse:
    """POST /pagamentos — calcula + persiste."""
    try:
        resposta = processar_pagamento(request)
    except PagamentoInvalidoError as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(erro),
        )

    salvar_pagamento(db, resposta, request.descricao)
    return resposta


@router.get(
    "/{pagamento_id}",
    response_model=PagamentoResponse,
    status_code=status.HTTP_200_OK,
    summary="Busca um pagamento pelo ID",
    description="Retorna os dados de um pagamento previamente persistido.",
)
def obter_pagamento(
    pagamento_id: UUID,
    db: Session = Depends(get_db),
) -> PagamentoResponse:
    """GET /pagamentos/{id} — busca pelo UUID, 404 se não achar."""
    pagamento_db = buscar_pagamento_por_id(db, pagamento_id)

    if pagamento_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pagamento não encontrado",
        )

    return PagamentoResponse.model_validate(pagamento_db)