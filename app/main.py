"""
Ponto de entrada da aplicação FastAPI.

Este módulo:
- Configura o logging estruturado (uma vez, no startup).
- Cria a instância FastAPI.
- Registra o middleware de Correlation ID.
- Cria as tabelas no banco (idempotente).
- Registra os routers do domínio.
"""
import logging

from fastapi import FastAPI

from app.api.routes_pagamento import router as pagamento_router
from app.db import models  # noqa: F401 — necessário pra registrar PagamentoDB no metadata
from app.db.database import Base, engine
from app.observabilidade.logging_config import configure_logging
from app.observabilidade.middleware import correlation_id_middleware

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

# Middleware: cross-cutting concern (correlation ID + log de request).
# Registrado ANTES dos routers — assim envelopa toda request.
app.middleware("http")(correlation_id_middleware)

# Routers de domínio.
app.include_router(pagamento_router)


@app.get("/health", tags=["Infraestrutura"])
def health_check() -> dict[str, str]:
    """
    Endpoint de verificação de saúde (versão simples — será enriquecida
    no Commit 4 com checks de banco e gateway).
    """
    return {"status": "ok"}


logger.info("app.startup.completo")