"""
Métricas Prometheus da aplicação.

Define os instrumentos (Counter, Histogram) e um middleware HTTP
que coleta métricas em toda request automaticamente.

Padrão profissional:
- Métricas com nome no formato `<sistema>_<unidade>_<sufixo>`
  (ex: http_requests_total, http_request_duration_seconds).
- Labels com baixa cardinalidade (method, endpoint TEMPLATE, status).
- NUNCA usar UUIDs ou IDs como labels — explode a cardinalidade.

Referência: Prometheus Naming Best Practices
https://prometheus.io/docs/practices/naming/
"""
import time

from prometheus_client import Counter, Histogram
from starlette.requests import Request

# ============================================================================
# Instrumentos.
# ============================================================================
# Counter: número total de requests HTTP, separado por método/rota/status.
# Sufixo "_total" é convenção do Prometheus pra Counters.
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total de requisições HTTP recebidas",
    ["method", "endpoint", "status"],
)

# Histogram: distribuição da duração das requests, em segundos.
# Sufixo "_seconds" é convenção pra unidade de tempo.
# Os buckets default do prometheus_client (5ms ... 10s) servem bem pra HTTP.
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duração das requisições HTTP em segundos",
    ["method", "endpoint"],
)


# ============================================================================
# Middleware de coleta.
# ============================================================================
async def metrics_middleware(request: Request, call_next):
    """
    Mede e conta TODA request HTTP que passa pela aplicação.

    Fluxo:
    1. Marca o tempo de início.
    2. Deixa a request seguir (call_next).
    3. Mede o tempo total.
    4. Incrementa o Counter e observa o Histogram.

    Cuidado com cardinalidade:
    - Usamos `request.scope["route"].path` (TEMPLATE da rota,
      ex: "/pagamentos/{pagamento_id}") e NÃO `request.url.path`
      (PATH bruto, ex: "/pagamentos/abc-123").
    - Sem isso, cada UUID viraria uma série temporal nova
      e estouraria a memória do Prometheus.
    """
    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    # Resolve o template da rota matched pelo FastAPI.
    # Fallback: se a rota não casou (404 puro), usa "unmatched"
    # pra evitar cardinalidade infinita.
    route = request.scope.get("route")
    endpoint = route.path if route is not None else "unmatched"

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=str(response.status_code),
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(duration)

    return response