"""
Ponto de entrada da aplicação FastAPI.

Este módulo:
- Configura o logging estruturado (uma vez, no startup).
- Cria a instância FastAPI.
- Registra os middlewares (Correlation ID + Métricas).
- Cria as tabelas no banco (idempotente).
- Registra os routers do domínio e de infraestrutura.
- Expõe o /health profundo (testa banco e gateway).
"""
import logging

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.routes_pagamento import router as pagamento_router
from app.core.config import settings
from app.db import models  # noqa: F401 — necessário pra registrar PagamentoDB no metadata
from app.db.database import Base, engine, ping_db
from app.observabilidade.logging_config import configure_logging
from app.observabilidade.metrics import metrics_middleware
from app.observabilidade.middleware import correlation_id_middleware
from app.observabilidade.routes_metrics import router as metrics_router

# ============================================================================
# Logging — configurado ANTES de qualquer outra coisa que possa logar.
# A partir daqui, qualquer logging.getLogger(__name__) já cospe JSON.
# ============================================================================
configure_logging()

logger = logging.getLogger(__name__)


# ============================================================================
# Banco — cria tabelas registradas em Base.metadata (idempotente).
# ============================================================================
Base.metadata.create_all(bind=engine)


# ============================================================================
# Aplicação FastAPI.
# ============================================================================
app = FastAPI(
    title="Microserviço de Pagamentos",
    description="API simulando processamento de pagamentos.",
    version="0.1.0",
)

# Middlewares: cross-cutting concerns. Registrados ANTES dos routers.
# Ordem de declaração importa: o ÚLTIMO registrado é o MAIS EXTERNO
# (executa primeiro no request, último no response).
app.middleware("http")(correlation_id_middleware)
app.middleware("http")(metrics_middleware)

# Routers — domínio + infraestrutura.
app.include_router(pagamento_router)
app.include_router(metrics_router)


# ============================================================================
# Health check profundo (Deep Health Check)
# ============================================================================
def _ping_gateway() -> bool:
    """
    Pinga o /health do fake_gateway via HTTP.

    Timeout curto (2s): health check não pode demorar — orquestrador
    aguarda no máximo poucos segundos antes de marcar o pod como doente.
    """
    try:
        url = f"{settings.gateway_url}/health"
        response = httpx.get(url, timeout=2.0)
        return response.status_code == 200
    except Exception as erro:
        logger.warning("health.gateway.ping_falhou", extra={"motivo": str(erro)})
        return False


@app.get(
    "/health",
    tags=["Infraestrutura"],
    summary="Deep health check (testa banco e gateway)",
)
def health_check() -> JSONResponse:
    """
    Verifica se a aplicação está pronta pra servir tráfego.

    Testa as dependências críticas:
    - database: SELECT 1 no Postgres
    - gateway: GET /health no fake_gateway

    Retorna:
    - 200 OK    → todas as dependências OK
    - 503       → uma ou mais dependências down (orquestrador retira
                  esse pod do load balancer)

    Padrão profissional: Liveness/Readiness Probe (Kubernetes / CNCF).
    """
    db_ok = ping_db()
    gateway_ok = _ping_gateway()

    checks = {
        "database": "ok" if db_ok else "down",
        "gateway": "ok" if gateway_ok else "down",
    }

    tudo_ok = db_ok and gateway_ok

    if tudo_ok:
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "checks": checks},
        )

    return JSONResponse(
        status_code=503,
        content={"status": "degraded", "checks": checks},
    )


logger.info("app.startup.completo")