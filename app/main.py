"""
Ponto de entrada da aplicação FastAPI.

Este módulo cria a instância principal do FastAPI e registra
as rotas (routers) que organizam os endpoints por domínio.

Executar com: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from app.api.routes_pagamento import router as pagamento_router

app = FastAPI(
    title="Microserviço de Pagamentos",
    description="API simulando processamento de pagamentos.",
    version="0.1.0",
)

# Registra o router de pagamentos na aplicação principal.
# Padrão profissional: main.py é um "registry" — só monta routers,
# não declara endpoints diretamente (exceto utilitários como /health).
app.include_router(pagamento_router)

@app.get("/health", tags=["Infraestrutura"])
def health_check() -> dict[str, str]:
    """
    Endpoint de verificação de saúde da aplicação.
    Usado por orquestradores (Kubernetes, Docker) para checar se o serviço está vivo.

    Retorna um JSON simples confirmando que o serviço está no ar.
    """
    return {"status": "ok"}