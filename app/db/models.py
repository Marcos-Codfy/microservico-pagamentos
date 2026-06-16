"""
Modelos ORM (SQLAlchemy) do domínio de pagamento.

Este módulo define como cada pagamento é estruturado no banco Postgres.
Não confundir com os schemas Pydantic em app/schemas/pagamento.py —
aqueles são contratos da API; estes aqui são linhas de tabela.

Princípio aplicado: separação DTO × Entidade Persistente (Clean Architecture).
A forma como o cliente HTTP vê o pagamento (PagamentoResponse) é
independente da forma como o banco armazena (PagamentoDB).
"""
from datetime import datetime, UTC
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class PagamentoDB(Base):
    """
    Modelo ORM da tabela `pagamentos` no Postgres.

    Cada instância representa uma linha persistida. O sufixo `DB` no
    nome da classe deixa explícito que é entidade de banco — distinto
    do schema Pydantic da camada da API.

    Campos:
        id: chave primária UUID, gerada no Python via uuid4.
        valor_total: valor original da compra (espelho do request).
        valor_parcela: valor de cada parcela já com juros aplicados.
        parcelas: número de parcelas (1 a 12).
        juros_aplicado: total de juros cobrados (0 se à vista ou 1-3x).
        valor_final: valor_total + juros_aplicado.
        metodo: método de pagamento ("cartao_credito", "pix", "boleto").
        status: resultado do processamento ("aprovado", "recusado", "pendente").
        descricao: descrição do pagamento (auditoria/extrato).
        criado_em: timestamp UTC tz-aware de criação.
    """

    __tablename__ = "pagamentos"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valor_parcela: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    parcelas: Mapped[int] = mapped_column(Integer)
    juros_aplicado: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    valor_final: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    metodo: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    descricao: Mapped[str] = mapped_column(String(200))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        """
        Representação textual da instância — útil para debug no PyCharm
        e em prints/logs. Sem isso, sairia algo como <PagamentoDB object
        at 0x7f8b1c0>, totalmente inútil.
        """
        return (
            f"<PagamentoDB id={self.id} "
            f"valor_final={self.valor_final} "
            f"status={self.status}>"
        )