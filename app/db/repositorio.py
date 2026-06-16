"""
Repositório de pagamentos — camada de persistência.

Este módulo é o "bibliotecário" do projeto. Sabe ARQUIVAR um pagamento
no Postgres (salvar) e BUSCAR um pagamento pelo identificador (carregar).
Não calcula juros, não valida HTTP, não conhece FastAPI.

Princípio aplicado: Repository Pattern (Eric Evans, DDD, 2003).
"""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PagamentoDB
from app.schemas.pagamento import PagamentoResponse


def salvar_pagamento(
    db: Session,
    pagamento_response: PagamentoResponse,
    descricao: str,
) -> PagamentoDB:
    """
    Persiste um pagamento processado no Postgres.

    Recebe o PagamentoResponse (que a calculadora devolveu) e a descricao
    (vinda do PagamentoRequest original). Os Enums (metodo, status) são
    gravados como string via `.value`, espelhando o modelo (String(20)).

    Args:
        db: Session ativa, injetada via Depends(get_db) na rota.
        pagamento_response: Resultado do processamento (já calculado).
        descricao: Texto descritivo do pagamento (vem do request).

    Returns:
        PagamentoDB persistido, com campos sincronizados com o Postgres.
    """
    pagamento_db = PagamentoDB(
        id=pagamento_response.id,
        valor_total=pagamento_response.valor_total,
        valor_parcela=pagamento_response.valor_parcela,
        parcelas=pagamento_response.parcelas,
        juros_aplicado=pagamento_response.juros_aplicado,
        valor_final=pagamento_response.valor_final,
        metodo=pagamento_response.metodo.value,
        status=pagamento_response.status.value,
        descricao=descricao,
        criado_em=pagamento_response.criado_em,
    )

    db.add(pagamento_db)        # intenção — marca pra inserir
    db.commit()                 # fato     — envia ao Postgres
    db.refresh(pagamento_db)    # confirmação — re-lê o que o banco gravou

    return pagamento_db


def buscar_pagamento_por_id(
    db: Session,
    pagamento_id: UUID,
) -> PagamentoDB | None:
    """
    Busca um pagamento pela chave primária (UUID).

    Usa a forma canônica do SQLAlchemy 2.0:
        select(Model).where(...).scalar_one_or_none()
    Funciona em qualquer contexto (rota HTTP, script standalone, teste) e
    é a base pra evoluir pra filtros mais complexos no futuro (joins,
    ordenação, paginação).

    Args:
        db: Session ativa.
        pagamento_id: UUID do pagamento procurado.

    Returns:
        PagamentoDB se encontrado, None caso contrário.
    """
    stmt = select(PagamentoDB).where(PagamentoDB.id == pagamento_id)
    return db.execute(stmt).scalar_one_or_none()