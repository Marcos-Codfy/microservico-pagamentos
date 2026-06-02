"""
Calculadora de pagamentos — lógica de negócio PURA.

Este módulo não importa nada de FastAPI ou de qualquer framework web.
Isso é proposital: a lógica de negócio é o "coração" da aplicação e
deve ser independente de como ela é exposta (HTTP, CLI, fila de mensagens).

Princípios aplicados:
- SRP (Single Responsibility Principle): só calcula. Não valida HTTP,
  não acessa banco, não loga, não envia email.
- DIP (Dependency Inversion): nada aqui depende da borda externa.
- Fail Fast: regras violadas lançam exceção imediatamente, em vez de
  retornar dados inválidos.
"""
from decimal import Decimal, ROUND_HALF_UP

from app.core.exceptions import PagamentoInvalidoError
from app.schemas.pagamento import (
    MetodoPagamento,
    PagamentoRequest,
    PagamentoResponse,
    StatusPagamento,
)

# Taxa de juros mensal aplicada em pagamentos parcelados no cartão.
# Em um sistema real, isso viria de configuração (env var) ou banco.
# Por enquanto, deixamos como constante para manter o foco no aprendizado.
TAXA_JUROS_MENSAL = Decimal("0.02")  # 2% ao mês (juros simples)

# Métodos que NÃO permitem parcelamento (sempre à vista).
METODOS_SEM_PARCELAMENTO = {MetodoPagamento.PIX, MetodoPagamento.BOLETO}


def _arredondar_para_centavos(valor: Decimal) -> Decimal:
    """
    Arredonda um Decimal para 2 casas decimais (centavos).

    Usa ROUND_HALF_UP (arredonda 0.5 para cima), que é o padrão
    contábil brasileiro. Padrão financeiro internacional pode usar
    ROUND_HALF_EVEN (banker's rounding), mas para nosso projeto
    didático ROUND_HALF_UP é mais intuitivo.

    Exemplo: Decimal("353.3333") → Decimal("353.33")
    """
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _validar_regras_negocio(request: PagamentoRequest) -> None:
    """
    Valida regras de negócio que não foram cobertas pelo Pydantic.

    O Pydantic já validou tipos e limites simples. Aqui tratamos
    regras que envolvem combinação de campos.

    Regras atuais:
    - PIX e Boleto não aceitam parcelamento (parcelas > 1).

    Args:
        request: Dados do pagamento a validar.

    Raises:
        PagamentoInvalidoError: Se alguma regra for violada.
    """
    if request.metodo in METODOS_SEM_PARCELAMENTO and request.parcelas > 1:
        raise PagamentoInvalidoError(
            f"O método {request.metodo.value} não permite parcelamento. "
            f"Use parcelas=1 ou escolha cartao_credito."
        )


def _calcular_juros(valor_total: Decimal, parcelas: int, metodo: MetodoPagamento) -> Decimal:
    """
    Calcula o valor total de juros do pagamento.

    Regras:
    - À vista (parcelas == 1): sem juros, retorna 0.
    - PIX ou Boleto: sem juros (já validamos que sempre será à vista).
    - Cartão parcelado: juros simples = valor × taxa × parcelas.

    Args:
        valor_total: Valor original da compra.
        parcelas: Número de parcelas.
        metodo: Método de pagamento.

    Returns:
        Valor total de juros a ser aplicado (já arredondado).
    """
    if parcelas == 1 or metodo != MetodoPagamento.CARTAO_CREDITO:
        return Decimal("0.00")

    juros = valor_total * TAXA_JUROS_MENSAL * Decimal(parcelas)
    return _arredondar_para_centavos(juros)


def processar_pagamento(request: PagamentoRequest) -> PagamentoResponse:
    """
    Processa um pedido de pagamento e devolve o resultado calculado.

    Fluxo:
    1. Valida regras de negócio (combinação método × parcelas).
    2. Calcula juros (se aplicável).
    3. Calcula valor final e valor da parcela.
    4. Monta e devolve o PagamentoResponse.

    Args:
        request: Dados do pagamento recebidos pela API.

    Returns:
        PagamentoResponse com os valores calculados e status APROVADO.

    Raises:
        PagamentoInvalidoError: Se alguma regra de negócio for violada.
    """
    # 1. Valida regras de negócio (pode lançar PagamentoInvalidoError)
    _validar_regras_negocio(request)

    # 2. Calcula juros
    juros_aplicado = _calcular_juros(
        valor_total=request.valor_total,
        parcelas=request.parcelas,
        metodo=request.metodo,
    )

    # 3. Calcula valor final e valor da parcela
    valor_final = _arredondar_para_centavos(request.valor_total + juros_aplicado)
    valor_parcela = _arredondar_para_centavos(valor_final / Decimal(request.parcelas))

    # 4. Monta o response (id e criado_em são gerados automaticamente)
    return PagamentoResponse(
        valor_total=request.valor_total,
        valor_parcela=valor_parcela,
        parcelas=request.parcelas,
        juros_aplicado=juros_aplicado,
        valor_final=valor_final,
        metodo=request.metodo,
        status=StatusPagamento.APROVADO,
    )