"""
Testes End-to-End (E2E) — sobem a app completa contra infraestrutura real.

Diferença vs integração:
- Integração: alguns componentes (gateway) são mockados via patch.
- E2E: NADA é mockado. Postgres real (porta 5433) + fake_gateway real (8001).

Marker @pytest.mark.e2e — permite filtrar suítes:
  pytest -v                  → roda tudo (19 + E2E)
  pytest -m e2e -v           → roda SÓ E2E
  pytest -m "not e2e" -v     → roda tudo MENOS E2E (loop rápido de dev)
"""
from decimal import Decimal

import httpx
import pytest

from app.core.config import settings


# Timeout do readiness probe no fake_gateway.
# Curto porque o container já deve estar UP via docker compose.
_GATEWAY_TIMEOUT_S = 5.0


@pytest.fixture(scope="module")
def gateway_pronto():
    """
    Readiness probe: confirma que o fake_gateway está respondendo em /health
    ANTES de rodar os testes E2E.

    Se a infraestrutura não estiver pronta, falha rápido com mensagem clara
    em vez de quebrar lá dentro do teste com 'ConnectionRefused' confuso.

    Scope='module': checagem é feita 1 vez por arquivo (não por teste).
    """
    url = f"{settings.gateway_url}/health"
    try:
        resposta = httpx.get(url, timeout=_GATEWAY_TIMEOUT_S)
        resposta.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError) as erro:
        pytest.fail(
            f"Fake gateway não está pronto em {url}. "
            f"Suba a infra com: docker compose up -d. Detalhe: {erro}"
        )
    yield


@pytest.mark.e2e
def test_e2e_criar_e_buscar_pagamento_atravessa_sistema_inteiro(
    client, gateway_pronto
):
    """
    Fluxo end-to-end realista: cria um pagamento e depois busca pelo ID.

    Caminho atravessado SEM nenhum mock:
        HTTP request
          → Pydantic (valida payload)
          → Calculadora (regras de negócio)
          → httpx (chamada real ao fake_gateway na 8001)
          → fake_gateway responde 'autorizado'
          → Repositório (SQLAlchemy)
          → Postgres real (porta 5433, tmpfs)
          → Response HTTP de volta ao cliente

    Bugs que esse teste pega e os outros não:
      - URL do gateway configurada errada no .env
      - Conversão Decimal/float entre app e gateway
      - Persistência real funcionando (escrita + leitura)
      - Round-trip de UUID via JSON
    """
    # ARRANGE — pedido cartão à vista (caminho feliz, sem juros)
    payload = {
        "valor_total": 1500.00,
        "parcelas": 1,
        "metodo": "cartao_credito",
        "descricao": "Teste E2E - fluxo completo",
    }

    # ACT 1 — cria o pagamento (POST atravessa tudo até o Postgres)
    resp_post = client.post("/pagamentos/", json=payload)

    # ASSERT 1 — criação aprovada e valores corretos
    assert resp_post.status_code == 201, resp_post.text
    body_post = resp_post.json()
    pagamento_id = body_post["id"]
    assert body_post["status"] == "aprovado"
    assert Decimal(body_post["valor_final"]) == Decimal("1500.00")
    assert Decimal(body_post["juros_aplicado"]) == Decimal("0.00")

    # ACT 2 — busca o MESMO pagamento (prova persistência real)
    resp_get = client.get(f"/pagamentos/{pagamento_id}")

    # ASSERT 2 — recurso encontrado e corpo consistente com o POST
    assert resp_get.status_code == 200
    body_get = resp_get.json()
    assert body_get["id"] == pagamento_id
    assert body_get["valor_final"] == body_post["valor_final"]
    assert body_get["metodo"] == "cartao_credito"