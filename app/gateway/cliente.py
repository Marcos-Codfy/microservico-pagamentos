"""
Cliente HTTP para o Fake Payment Gateway.

Esta é a CAMADA DE BORDA
qualquer comunicação com o mundo externo (gateway) entra e sai daqui.
O domínio nunca sabe que existe HTTP, JSON ou httpx por baixo.

Por que isolar:
- Trocar o gateway (Mercado Pago, Stripe, ...) muda só este arquivo.
- Mockar nos testes vira trivial (substitui esta função).
- Tratamento de erros HTTP (timeout, 5xx, 4xx) fica concentrado aqui.
- Propagação de correlation ID acontece aqui — uma vez, pra toda
  chamada externa.
"""
import logging
from decimal import Decimal

import httpx

from app.core.config import settings
from app.core.exceptions import (
    GatewayIndisponivelError,
    GatewayRecusouPagamentoError,
)
from app.observabilidade.middleware import HEADER_NAME, request_id_ctx_var


# Timeout explícito: nunca deixar uma chamada HTTP travar indefinidamente.
# 5s é generoso para um gateway local, agressivo para um real.
_TIMEOUT_SEGUNDOS = 5.0


logger = logging.getLogger(__name__)


def autorizar_pagamento(valor: Decimal, metodo: str) -> str:
    """
    Solicita autorização do pagamento no gateway externo.

    Propaga o X-Request-ID atual no header da chamada — é assim que
    o correlation ID atravessa a fronteira do nosso microserviço e
    permite rastrear a transação no log do gateway também.

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

    # Pega o request_id atual do contextvar — setado pelo middleware
    # logo na entrada do request HTTP. Default "-" se chamada vier
    # de fora de um request (ex.: script, background job).
    request_id = request_id_ctx_var.get()
    headers = {HEADER_NAME: request_id}

    logger.info(
        "gateway.chamada.iniciada",
        extra={"valor": float(valor), "metodo": metodo},
    )

    try:
        response = httpx.post(
            url,
            json=payload,
            headers=headers,
            timeout=_TIMEOUT_SEGUNDOS,
        )
    except httpx.RequestError as erro:
        # Cobre: timeout, DNS falhou, conexão recusada, rede caiu.
        logger.error(
            "gateway.indisponivel",
            extra={"motivo": str(erro)},
        )
        raise GatewayIndisponivelError(
            f"Falha de comunicação com o gateway: {erro}"
        )

    # 5xx do gateway = problema do lado deles, semanticamente "indisponível".
    if response.status_code >= 500:
        logger.error(
            "gateway.erro_5xx",
            extra={"status_code": response.status_code},
        )
        raise GatewayIndisponivelError(
            f"Gateway respondeu com erro {response.status_code}"
        )

    # 4xx do gateway = pagamento recusado pelas regras deles.
    if response.status_code >= 400:
        logger.warning(
            "gateway.recusado_4xx",
            extra={"status_code": response.status_code},
        )
        raise GatewayRecusouPagamentoError(
            f"Gateway recusou o pagamento (HTTP {response.status_code})"
        )

    dados = response.json()

    # Gateway real pode devolver 200 OK com autorizado=False (recusa "macia").
    # Tratamos os dois caminhos para não cair em surpresa em produção.
    if not dados.get("autorizado", False):
        logger.warning("gateway.nao_autorizado")
        raise GatewayRecusouPagamentoError("Gateway não autorizou o pagamento")

    logger.info(
        "gateway.autorizado",
        extra={"transacao_id": dados["transacao_id"]},
    )
    return dados["transacao_id"]