"""
Testes unitários da calculadora de pagamentos.

Estes testes exercitam APENAS a lógica de negócio pura (camada `core`),
sem subir servidor HTTP nem tocar em banco de dados — por isso são
testes UNITÁRIOS (rápidos, isolados, determinísticos).

Padrão usado em todos os testes: AAA (Arrange / Act / Assert).
- Arrange: preparar os dados de entrada.
- Act: executar a função sob teste.
- Assert: comparar o resultado obtido com o esperado.

Cada teste cobre um cenário diferente da matriz de decisão:
- Boundary inferior do cartão (1x — ainda sem juros).
- Boundary superior do cartão (12x — limite máximo da regra).
- Regra de negócio violada (PIX parcelado → exceção).
"""

from decimal import Decimal

import pytest

from app.core.calculadora import processar_pagamento
from app.core.exceptions import PagamentoInvalidoError
from app.schemas.pagamento import MetodoPagamento, PagamentoRequest


def test_cartao_a_vista_nao_aplica_juros() -> None:
    """Cartão em 1x não deve cobrar juros."""
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
    """Cartão em 12x (limite do schema) deve aplicar 24% de juros (2% × 12)."""
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
    """PIX com mais de 1 parcela deve lançar exceção de domínio."""
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