"""
Schemas (contratos de dados) do domínio de pagamento.

Usamos Pydantic para validar automaticamente os dados que entram
e saem da API. Decimal é usado para precisão monetária — float
NUNCA deve ser usado para dinheiro.

Princípio aplicado: DTOs separados para entrada (Request) e saída (Response).
Isso protege a API contra vazamento de dados sensíveis e permite que cada
contrato evolua de forma independente.
"""
from datetime import datetime, UTC
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class MetodoPagamento(str, Enum):
    """
    Enumeração dos métodos de pagamento aceitos.

    Herdar de `str` permite que o valor seja serializado
    como string no JSON da API.
    """
    CARTAO_CREDITO = "cartao_credito"
    PIX = "pix"
    BOLETO = "boleto"


class StatusPagamento(str, Enum):
    """
    Enumeração dos possíveis status de um pagamento processado.

    - APROVADO: pagamento aceito e processado com sucesso.
    - RECUSADO: pagamento rejeitado (por regra de negócio ou validação).
    - PENDENTE: aguardando confirmação (ex.: boleto não pago ainda).
    """
    APROVADO = "aprovado"
    RECUSADO = "recusado"
    PENDENTE = "pendente"


class PagamentoRequest(BaseModel):
    """
    Dados recebidos pela API ao criar um pagamento.

    Validações aplicadas automaticamente pelo Pydantic:
    - valor_total: precisa ser > 0
    - parcelas: precisa estar entre 1 e 12
    - metodo: precisa ser um dos valores do Enum
    - descricao: entre 3 e 200 caracteres
    """
    valor_total: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Valor total da compra em reais. Ex.: 1500.00",
    )
    parcelas: int = Field(
        ...,
        ge=1,
        le=12,
        description="Número de parcelas (1 = à vista).",
    )
    metodo: MetodoPagamento = Field(
        ...,
        description="Método de pagamento escolhido.",
    )
    descricao: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Descrição do pagamento.",
    )


class PagamentoResponse(BaseModel):
    """
    Dados retornados pela API após processar um pagamento.

    Contém informações enriquecidas pelo backend:
    - id: identificador único da transação (gerado pelo servidor)
    - valor_parcela: calculado a partir do valor_total e parcelas
    - juros_aplicado: valor cobrado de juros (0 se à vista ou sem juros)
    - valor_final: valor_total + juros_aplicado (o que o cliente paga de fato)
    - status: resultado do processamento
    - criado_em: timestamp UTC de criação (auditoria)
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(
        default_factory=uuid4,
        description="Identificador único da transação.",
    )
    valor_total: Decimal = Field(
        ...,
        description="Valor original da compra (eco do request).",
    )
    valor_parcela: Decimal = Field(
        ...,
        description="Valor de cada parcela já com juros (se houver).",
    )
    parcelas: int = Field(
        ...,
        description="Número de parcelas aplicado.",
    )
    juros_aplicado: Decimal = Field(
        ...,
        description="Valor total de juros cobrados (0 se à vista).",
    )
    valor_final: Decimal = Field(
        ...,
        description="Valor total final a ser pago (valor_total + juros_aplicado).",
    )
    metodo: MetodoPagamento = Field(
        ...,
        description="Método de pagamento utilizado.",
    )
    status: StatusPagamento = Field(
        ...,
        description="Status do processamento do pagamento.",
    )
    criado_em: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Data e hora UTC de criação do pagamento.",
    )