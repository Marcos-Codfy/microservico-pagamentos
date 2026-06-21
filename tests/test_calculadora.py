"""
Testes unitários da calculadora — lógica pura, sem HTTP, sem banco.

Estratégia de cobertura (caixa-preta):
- Boundary Value Analysis (BVA): testar fronteiras onde a regra muda (1x, 3x, 4x, 12x).
- Equivalence Partitioning: pelo menos 1 representante de cada família (cartão / PIX / Boleto).
- Decision Table: combinação método × parcelas sem combos válidos/inválidos escapando.

Defesa contra mutação (mutmut):
- Verificação explícita do `status` da resposta.
- Comparação de string EXATA na mensagem de erro (regex frouxo deixa passar
  mutações com sufixo/prefixo — comparação exata é binária).

Padrão AAA aplicado em todos os testes.
"""

from decimal import Decimal

import pytest

from app.core.calculadora import processar_pagamento
from app.core.exceptions import PagamentoInvalidoError
from app.schemas.pagamento import (
    MetodoPagamento,
    PagamentoRequest,
    StatusPagamento,
)


# ============================================================
# Cartão de crédito — limites de juros (BVA)
# ============================================================

def test_cartao_a_vista_nao_aplica_juros() -> None:
    """Cartão 1x: boundary inferior, sem juros."""
    request = PagamentoRequest(
        valor_total=Decimal("1000.00"),
        parcelas=1,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão à vista",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("0.00")
    assert resposta.valor_final == Decimal("1000.00")


def test_cartao_3x_nao_aplica_juros() -> None:
    """Cartão 3x: último valor sem juros (PARCELAS_SEM_JUROS_MAX)."""
    request = PagamentoRequest(
        valor_total=Decimal("900.00"),
        parcelas=3,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão 3x sem juros",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("0.00")
    assert resposta.valor_final == Decimal("900.00")
    assert resposta.valor_parcela == Decimal("300.00")


def test_cartao_4x_aplica_juros() -> None:
    """Cartão 4x: primeiro valor COM juros. Juros: 1000 × 0,02 × 4 = 80,00."""
    request = PagamentoRequest(
        valor_total=Decimal("1000.00"),
        parcelas=4,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão 4x com juros",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("80.00")
    assert resposta.valor_final == Decimal("1080.00")
    assert resposta.valor_parcela == Decimal("270.00")


def test_cartao_12x_aplica_juros_no_limite_maximo() -> None:
    """Cartão 12x: boundary superior do schema. Juros: 1000 × 0,02 × 12 = 240."""
    request = PagamentoRequest(
        valor_total=Decimal("1000.00"),
        parcelas=12,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão parcelado no limite",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("240.00")
    assert resposta.valor_final == Decimal("1240.00")


# ============================================================
# PIX e Boleto — caminho feliz e regra de negócio
# ============================================================

def test_pix_a_vista_processa_normalmente() -> None:
    """PIX 1x: caminho feliz, sem juros."""
    request = PagamentoRequest(
        valor_total=Decimal("250.00"),
        parcelas=1,
        metodo=MetodoPagamento.PIX,
        descricao="PIX à vista",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("0.00")
    assert resposta.valor_final == Decimal("250.00")
    assert resposta.metodo == MetodoPagamento.PIX


def test_boleto_a_vista_processa_normalmente() -> None:
    """Boleto 1x: caminho feliz, sem juros."""
    request = PagamentoRequest(
        valor_total=Decimal("780.50"),
        parcelas=1,
        metodo=MetodoPagamento.BOLETO,
        descricao="Boleto à vista",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("0.00")
    assert resposta.valor_final == Decimal("780.50")
    assert resposta.metodo == MetodoPagamento.BOLETO


def test_pix_parcelado_lanca_pagamento_invalido_error() -> None:
    """PIX parcelado viola regra de negócio → exceção."""
    request = PagamentoRequest(
        valor_total=Decimal("500.00"),
        parcelas=3,
        metodo=MetodoPagamento.PIX,
        descricao="PIX parcelado",
    )

    with pytest.raises(PagamentoInvalidoError):
        processar_pagamento(request)


def test_boleto_parcelado_lanca_pagamento_invalido_error() -> None:
    """Boleto parcelado viola regra de negócio → exceção."""
    request = PagamentoRequest(
        valor_total=Decimal("780.50"),
        parcelas=2,
        metodo=MetodoPagamento.BOLETO,
        descricao="Boleto parcelado (inválido)",
    )

    with pytest.raises(PagamentoInvalidoError):
        processar_pagamento(request)


# ============================================================
# Precisão decimal e arredondamento (ROUND_HALF_UP)
# ============================================================

def test_cartao_com_valor_decimal_calcula_corretamente() -> None:
    """Cartão 4x com R$ 333,33. Juros: 26,6664 → 26,67 (3ª casa = 6, arredonda pra cima)."""
    request = PagamentoRequest(
        valor_total=Decimal("333.33"),
        parcelas=4,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão 4x com valor decimal",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("26.67")
    assert resposta.valor_final == Decimal("360.00")
    assert resposta.valor_parcela == Decimal("90.00")


def test_arredondamento_aplica_round_half_up() -> None:
    """Cartão 5x com R$ 100,12. Força ROUND_HALF_UP na parcela (22,026 → 22,03)."""
    request = PagamentoRequest(
        valor_total=Decimal("100.12"),
        parcelas=5,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Teste arredondamento",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("10.01")
    assert resposta.valor_final == Decimal("110.13")
    assert resposta.valor_parcela == Decimal("22.03")


# ============================================================
# Defesa contra mutação — campos críticos da resposta
# ============================================================

def test_cartao_a_vista_retorna_status_aprovado() -> None:
    """
    Garante explicitamente que `status == APROVADO` no caminho feliz.

    Os testes anteriores verificam valores monetários mas NÃO o campo `status`.
    Em pagamento, status é a informação de mais alto impacto da resposta —
    APROVADO virando RECUSADO silenciosamente seria catastrófico.
    """
    request = PagamentoRequest(
        valor_total=Decimal("1000.00"),
        parcelas=1,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Garantia de status aprovado",
    )

    resposta = processar_pagamento(request)

    assert resposta.status == StatusPagamento.APROVADO


def test_pix_parcelado_mensagem_de_erro_e_exata() -> None:
    """
    Mata mutações no CONTEÚDO da mensagem de erro (mutmut #11 e #12).

    Por que comparação exata em vez de regex:
    - Mutmut injeta `XX...XX` em strings; regex frouxo com `.*` deixa passar.
    - Comparação binária (`==`) falha imediatamente com qualquer caractere extra.

    Por que mensagem importa em pagamentos:
    - Logs de auditoria precisam do motivo claro.
    - FastAPI propaga essa string como `detail` no HTTP 422.
    """
    request = PagamentoRequest(
        valor_total=Decimal("500.00"),
        parcelas=3,
        metodo=MetodoPagamento.PIX,
        descricao="PIX parcelado com mensagem verificada",
    )

    with pytest.raises(PagamentoInvalidoError) as exc_info:
        processar_pagamento(request)

    assert str(exc_info.value) == (
        "O método pix não permite parcelamento. "
        "Use parcelas=1 ou escolha cartao_credito."
    )