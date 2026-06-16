"""
Testes de integração da API de pagamentos.

Cada teste é ISOLADO pela fixture `client`:
- Banco de teste zerado (Postgres porta 5433, tmpfs)
- `get_db` substituído pela sessão de teste
- FastAPI em memória via TestClient

Para cenários de falha do gateway externo, usamos
unittest.mock.patch — não precisamos derrubar containers,
nem depender de comportamento do fake_gateway.

Padrão AAA: Arrange (preparar) → Act (executar) → Assert (validar).
"""
from unittest.mock import patch

from app.core.exceptions import (
    GatewayIndisponivelError,
    GatewayRecusouPagamentoError,
)


# ============================================================
# Helpers — payloads reutilizáveis (DRY)
# ============================================================
def _payload_cartao_a_vista():
    return {
        "valor_total": 100.00,
        "parcelas": 1,
        "metodo": "cartao_credito",
        "descricao": "teste cartao a vista",
    }


# ============================================================
# POST /pagamentos/ — fluxo feliz (201)
# ============================================================
def test_post_cartao_a_vista_devolve_201(client):
    """Cenário mais simples: cartão à vista, sem juros."""
    # Act
    response = client.post("/pagamentos/", json=_payload_cartao_a_vista())

    # Assert
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "aprovado"
    assert float(body["valor_final"]) == 100.00
    assert body["parcelas"] == 1


def test_post_cartao_parcelado_aplica_juros(client):
    """Cartão 6x: deve aplicar juros e valor_final > valor_total."""
    # Arrange
    payload = {
        "valor_total": 1000.00,
        "parcelas": 6,
        "metodo": "cartao_credito",
        "descricao": "cartao 6x com juros",
    }

    # Act
    response = client.post("/pagamentos/", json=payload)

    # Assert
    assert response.status_code == 201
    body = response.json()
    assert float(body["juros_aplicado"]) > 0
    assert float(body["valor_final"]) > 1000.00


# ============================================================
# POST /pagamentos/ — regras de negócio violadas (422)
# ============================================================
def test_post_pix_parcelado_devolve_422(client):
    """PIX não permite parcelas > 1. Regra do domínio."""
    # Arrange
    payload = {
        "valor_total": 100.00,
        "parcelas": 3,
        "metodo": "pix",
        "descricao": "pix nao aceita parcela",
    }

    # Act
    response = client.post("/pagamentos/", json=payload)

    # Assert
    assert response.status_code == 422
    assert "pix" in response.json()["detail"].lower()


def test_post_payload_invalido_devolve_422(client):
    """Falta o campo 'descricao' — Pydantic barra antes da rota."""
    # Arrange: payload incompleto
    payload = {
        "valor_total": 100.00,
        "parcelas": 1,
        "metodo": "cartao_credito",
    }

    # Act
    response = client.post("/pagamentos/", json=payload)

    # Assert: Pydantic devolve 422 com lista de campos faltando
    assert response.status_code == 422


# ============================================================
# POST /pagamentos/ — falhas do gateway externo (MOCK)
# ============================================================
def test_post_gateway_indisponivel_devolve_503(client):
    """Gateway fora do ar deve virar HTTP 503."""
    # Arrange: substitui autorizar_pagamento por uma versão que
    # SEMPRE levanta GatewayIndisponivelError (gateway off).
    with patch(
        "app.api.routes_pagamento.autorizar_pagamento",
        side_effect=GatewayIndisponivelError("simulando gateway offline"),
    ):
        # Act
        response = client.post("/pagamentos/", json=_payload_cartao_a_vista())

    # Assert
    assert response.status_code == 503
    assert "gateway" in response.json()["detail"].lower()


def test_post_gateway_recusou_devolve_402(client):
    """Gateway respondeu mas recusou: HTTP 402 Payment Required."""
    # Arrange
    with patch(
        "app.api.routes_pagamento.autorizar_pagamento",
        side_effect=GatewayRecusouPagamentoError("cartao sem saldo"),
    ):
        # Act
        response = client.post("/pagamentos/", json=_payload_cartao_a_vista())

    # Assert
    assert response.status_code == 402


# ============================================================
# GET /pagamentos/{id}
# ============================================================
def test_get_pagamento_existente_devolve_200(client):
    """Cria via POST, depois busca via GET — round-trip completo."""
    # Arrange: cria um pagamento
    post_response = client.post("/pagamentos/", json=_payload_cartao_a_vista())
    assert post_response.status_code == 201
    pagamento_id = post_response.json()["id"]

    # Act: busca pelo ID retornado
    get_response = client.get(f"/pagamentos/{pagamento_id}")

    # Assert
    assert get_response.status_code == 200
    assert get_response.json()["id"] == pagamento_id
    assert float(get_response.json()["valor_final"]) == 100.00


def test_get_pagamento_inexistente_devolve_404(client):
    """UUID válido mas que não existe no banco."""
    uuid_inexistente = "00000000-0000-0000-0000-000000000000"

    response = client.get(f"/pagamentos/{uuid_inexistente}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Pagamento não encontrado"


def test_get_pagamento_uuid_invalido_devolve_422(client):
    """String que não é UUID — Pydantic barra antes da rota."""
    response = client.get("/pagamentos/nao-eh-uuid")

    assert response.status_code == 422