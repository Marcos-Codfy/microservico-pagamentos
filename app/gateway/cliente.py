"""
Cliente HTTP para o Fake Payment Gateway.

Esta é a CAMADA DE BORDA (Anti-Corruption Layer):
qualquer comunicação com o mundo externo (gateway) entra e sai daqui.
O domínio nunca sabe que existe HTTP, JSON ou httpx por baixo.

Por que isolar:
- Trocar o gateway (Mercado Pago, Stripe, ...) muda só este arquivo.
- Mockar nos testes vira trivial (substitui esta função).
- Tratamento de erros HTTP (timeout, 5xx, 4xx) fica concentrado aqui.
"""
from decimal import Decimal

import httpx

from app.core.config import settings
from app.core.exceptions import (
    GatewayIndisponivelError,
    GatewayRecusouPagamentoError,
)


# Timeout explícito: nunca deixar uma chamada HTTP travar indefinidamente.
# 5s é generoso para um gateway local, agressivo para um real.
_TIMEOUT_SEGUNDOS = 5.0


def autorizar_pagamento(valor: Decimal, metodo: str) -> str:
    """
    Solicita autorização do pagamento no gateway externo.

    Args:
        valor: valor final do pagamento (já com juros, se houver).
        metodo: "cartao" | "pix" | "boleto".

    Returns:
        transacao_id devolvido pelo gateway (string).

    Raises:
        GatewayIndisponivelError: gateway fora do ar, timeout ou 5xx.
        GatewayRecusouPagamentoError: gateway respondeu mas recusou.
    """
    url = f"{settings.gateway_url}/autorizar"
    payload = {"valor": float(valor), "metodo": metodo}

    try:
        response = httpx.post(url, json=payload, timeout=_TIMEOUT_SEGUNDOS)
    except httpx.RequestError as erro:
        # Cobre: timeout, DNS falhou, conexão recusada, rede caiu.
        raise GatewayIndisponivelError(
            f"Falha de comunicação com o gateway: {erro}"
        )

    # 5xx do gateway = problema do lado deles, semanticamente "indisponível".
    if response.status_code >= 500:
        raise GatewayIndisponivelError(
            f"Gateway respondeu com erro {response.status_code}"
        )

    # 4xx do gateway = pagamento recusado pelas regras deles.
    if response.status_code >= 400:
        raise GatewayRecusouPagamentoError(
            f"Gateway recusou o pagamento (HTTP {response.status_code})"
        )

    dados = response.json()

    # Gateway real pode devolver 200 OK com autorizado=False (recusa "macia").
    # Tratamos os dois caminhos para não cair em surpresa em produção.
    if not dados.get("autorizado", False):
        raise GatewayRecusouPagamentoError("Gateway não autorizou o pagamento")

    return dados["transacao_id"]