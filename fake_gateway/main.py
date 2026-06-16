"""
Fake Payment Gateway - simula um gateway externo (tipo Mercado Pago)

Roda em container isolado na porta 8001. Sempre autoriza pagamentos.
Cenários de falha (recusa, indisponibilidade), serão simulados via mock
nos testes da Sessão 3, sem precisar mexer aqui.
"""

from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Fake Payment Gateway",
    version="0.1.0",

)

class AutorizacaoRequest(BaseModel):
    valor: float
    metodo: str


class AutorizacaoResponse(BaseModel):
    autorizado: bool
    transacao_id: str


@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/autorizar", response_model=AutorizacaoResponse)
def autorizar(request: AutorizacaoRequest) -> AutorizacaoResponse:
    return AutorizacaoResponse(
        autorizado=True,
        transacao_id=f"fake-{uuid4()}"
    )