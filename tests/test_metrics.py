"""
Testes do endpoint /metrics.

Valida:
- Endpoint responde 200.
- Content-Type é o oficial do Prometheus.
- Body contém as métricas que registramos no metrics.py.

Padrão AAA: Arrange / Act / Assert.
"""


def test_metrics_endpoint_devolve_formato_prometheus(client):
    """
    Garante que /metrics está exposto e devolve as métricas no formato certo.

    Arrange: dispara uma request leve (422) pra forçar o middleware a registrar
             pelo menos 1 observação ANTES da gente ler /metrics.
    Act:     bate em /metrics.
    Assert:  status 200, content-type Prometheus, e os nomes das métricas
             estão presentes no body.
    """
    # Arrange — gera 1 amostra. UUID inválido devolve 422 sem tocar DB nem gateway.
    client.get("/pagamentos/nao-eh-um-uuid-valido")

    # Act
    response = client.get("/metrics")

    # Assert
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]

    body = response.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body