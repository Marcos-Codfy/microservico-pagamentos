"""
Endpoint /metrics — expõe métricas no formato Prometheus.

O Prometheus server faz scraping desse endpoint periodicamente
(por padrão a cada 15s) e armazena os valores no banco de séries
temporais dele.

Padrão profissional: Pull-based monitoring (Prometheus).
Diferente de Push (StatsD, Graphite) — aqui a aplicação só EXPÕE,
o servidor é que VEM BUSCAR. Vantagem: a aplicação não precisa
conhecer o endereço do coletor.
"""
from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["Infraestrutura"])


@router.get(
    "/metrics",
    summary="Métricas no formato Prometheus",
    description="Endpoint scrapado pelo Prometheus server. Formato texto puro.",
    response_class=Response,
)
def metrics() -> Response:
    """
    Gera o snapshot atual de TODAS as métricas registradas.

    - `generate_latest()` retorna bytes no formato Prometheus Exposition.
    - `CONTENT_TYPE_LATEST` é o media-type oficial
      ("text/plain; version=0.0.4; charset=utf-8").
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )