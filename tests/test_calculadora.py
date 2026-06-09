"""
Testes unitários da calculadora — lógica pura, sem HTTP, sem banco.

Padrão AAA (Arrange / Act / Assert) em todos os testes.

Estratégia de cobertura (caixa-preta):
- Boundary Value Analysis (BVA): testar as fronteiras onde a regra
  muda de comportamento (1x, 3x, 4x, 12x).
- Equivalence Partitioning: ter pelo menos 1 representante de cada
  família (cartão / PIX / Boleto).
- Decision Table: combinar método × parcelas garantindo que nenhum
  combo válido ou inválido escape sem teste.

Regras de negócio cobertas:
- Cartão 1x a 3x: sem juros.
- Cartão 4x a 12x: juros simples = valor × 0,02 × parcelas.
- PIX e Boleto: aceitam APENAS parcelas=1 (acima disso → exceção).
- Arredondamento monetário: ROUND_HALF_UP (padrão contábil BR).
"""

from decimal import Decimal, ROUND_HALF_UP
import pytest

from app.core.calculadora import processar_pagamento
from app.core.exceptions import PagamentoInvalidoError
from app.schemas.pagamento import MetodoPagamento, PagamentoRequest


def test_cartao_a_vista_nao_aplica_juros() -> None:
    """Cartão em 1x não deve cobrar juros (boundary inferior sem juros)."""
    # Arrange
    request = PagamentoRequest(
        valor_total=Decimal("1000.00"),
        parcelas=1,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão à vista",
    )

    # Act
    resposta = processar_pagamento(request)

    # Assert
    assert resposta.juros_aplicado == Decimal("0.00")
    assert resposta.valor_final == Decimal("1000.00")


def test_cartao_12x_aplica_juros_no_limite_maximo() -> None:
    """Cartão em 12x (limite superior do schema) deve aplicar 24% de juros (2% × 12)."""
    # Arrange
    request = PagamentoRequest(
        valor_total=Decimal("1000.00"),
        parcelas=12,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão parcelado no limite",
    )

    # Act
    resposta = processar_pagamento(request)

    # Assert
    assert resposta.juros_aplicado == Decimal("240.00")
    assert resposta.valor_final == Decimal("1240.00")


def test_pix_parcelado_lanca_pagamento_invalido_error() -> None:
    """PIX com mais de 1 parcela deve viola a regra de negocio -> execção de domínio."""
    # Arrange
    request = PagamentoRequest(
        valor_total=Decimal("500.00"),
        parcelas=3,
        metodo=MetodoPagamento.PIX,
        descricao="PIX parcelado",
    )

    # Act + Assert
    with pytest.raises(PagamentoInvalidoError):
        processar_pagamento(request)


def test_cartao_3x_não_aplica_juros() -> None:
    """
    Cartão em 3x: Boundary do ultimo valor sem juros

    Esse teste protege contra erro clássico do codigo:
    se alguém trocar 'parcelas <= PARCELAS_SEM_JUROS_MAX' por
    'parcelas' < PARCELAS_SEM_JUROS_MAX', este teste vermelha.
    """

    #Arrange
    request = PagamentoRequest(
        valor_total=Decimal("900.00"),
        parcelas=3,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão 3x sem juros",
    )

    #Act
    resposta = processar_pagamento(request)

    #Assert
    assert resposta.juros_aplicado == Decimal("0.00")
    assert resposta.valor_final == Decimal("900.00")
    assert resposta.valor_parcela == Decimal("300.00")


def test_cartao_4x_aplica_juros() -> None:
    """
    Cartão em 4x: Boundary do Primeiro valor sem juros.

    Cálculo esperado:
    - Juros: 1000,00 × 0,02 × 4 = 80,00
    - Valor final: 1000,00 + 80,00 = 1080,00
    - Parcela: 1080,00 / 4 = 270,00
    """

    #Arrange
    request = PagamentoRequest(
        valor_total=Decimal("1000.00"),
        parcelas=4,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão 4x com juros"
    )

    #Act
    resposta = processar_pagamento(request)


    #Assert
    assert resposta.juros_aplicado == Decimal("80.00")
    assert resposta.valor_final == Decimal("1080.00")
    assert resposta.valor_parcela == Decimal("270.00")


def test_pix_a_vista_processa_normalmente() -> None:
    """
    PIX em 1x: cmainho feliz - sem juros, status APROVADO
    """
    request = PagamentoRequest(
        valor_total=Decimal("250.00"),
        parcelas=1,
        metodo=MetodoPagamento.PIX,
        descricao="PIX á vista",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("0.00")
    assert resposta.valor_final == Decimal("250.00")
    assert resposta.metodo == MetodoPagamento.PIX


def test_boleto_a_vista_processa_normalmente() -> None:
    """Boleto em 1x: caminho Feliz - sem juros, status APROVADO """

    request = PagamentoRequest(
        valor_total=Decimal("780.50"),
        parcelas=1,
        metodo=MetodoPagamento.BOLETO,
        descricao="Boleto a vista"
    )


    resposta = processar_pagamento(request)


    assert resposta.juros_aplicado == Decimal("0.00")
    assert resposta.valor_final == Decimal("780.50")
    assert resposta.metodo == MetodoPagamento.BOLETO


def test_boleto_parcelado_lanca_pagamento_invalido_error() -> None:
    """Boleto com mais de 1 parcela viola a regra de negocio -> exceção"""

    request = PagamentoRequest(
        valor_total=Decimal("780.50"),
        parcelas=2,
        metodo=MetodoPagamento.BOLETO,
        descricao="Boleto parcelado (invalido)"
    )

    with pytest.raises(PagamentoInvalidoError):
        processar_pagamento(request)


# Testes novos — precisão decimal e arredondamento

def test_cartao_com_valor_decimal_calcula_corretamente() -> None:
    """
     Cartão 4x com valor R$ 333,33 — testa precisão do Decimal.

    Cálculo esperado:
    - Juros bruto: 333,33 × 0,02 × 4 = 26,6664
    - Juros arredondado (ROUND_HALF_UP, 3ª casa = 6): 26,67
    - Valor final: 333,33 + 26,67 = 360,00
    - Parcela: 360,00 / 4 = 90,00
    """

    request = PagamentoRequest(
        valor_total=Decimal("333.33"),
        parcelas=4,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Cartão 4x com valor decimal"
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("26.67")
    assert resposta.valor_final == Decimal("360.00")
    assert resposta.valor_parcela == Decimal("90.00")


def test_arrendodamento_aplica_round_half_up() -> None:
    """
    Cartão 5x com R$ 100,12 — força ROUND_HALF_UP na parcela.

    Cálculo esperado:
    - Juros bruto: 100,12 × 0,02 × 5 = 10,012
    - Juros arredondado (3ª casa = 2, arredonda pra baixo): 10,01
    - Valor final: 100,12 + 10,01 = 110,13
    - Parcela bruta: 110,13 / 5 = 22,026
    - Parcela arredondada (3ª casa = 6, arredonda pra cima): 22,03
    """

    request = PagamentoRequest(
        valor_total=Decimal("100.12"),
        parcelas=5,
        metodo=MetodoPagamento.CARTAO_CREDITO,
        descricao="Teste arrendodamento",
    )

    resposta = processar_pagamento(request)

    assert resposta.juros_aplicado == Decimal("10.01")
    assert resposta.valor_final == Decimal("110.13")
    assert resposta.valor_parcela == Decimal("22.03")