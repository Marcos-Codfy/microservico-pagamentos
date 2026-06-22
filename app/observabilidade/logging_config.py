"""
Configuração centralizada do logging estruturado em JSON.

Princípio: One Configuration Point. O logging é configurado UMA VEZ
no startup, no root logger. Todos os módulos do projeto (`logger =
logging.getLogger(__name__)`) herdam dessa config automaticamente.

Saída padrão: JSON em stdout. Pronto pra ser coletado por agentes
(Datadog, Splunk, CloudWatch Logs, Loki) sem nenhum parser custom.
"""
import logging
import sys

from pythonjsonlogger import jsonlogger

from app.observabilidade.middleware import request_id_ctx_var


class CorrelationIdFilter(logging.Filter):
    """
    Injeta o request_id (vindo do contextvars) em cada LogRecord.

    `Filter` no módulo logging tem duas funções:
      - Retornar False = descartar o log
      - Mutar o `record` antes do formatter ver = enriquecer

    Aqui usamos a segunda função: pegamos o request_id atual do contextvar
    e colamos no record. Quando o JsonFormatter for serializar, vai
    encontrar o campo "request_id" e jogar no JSON automaticamente.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get()
        return True  # True = mantém o log (não descarta)


def configure_logging() -> None:
    """
    Configura o root logger pra emitir JSON estruturado em stdout.

    Deve ser chamado UMA vez, bem cedo no startup (ver `app/main.py`).
    Idempotente: limpa handlers anteriores antes de instalar o novo.
    """
    # Handler: pra onde vai a saída? Stdout (padrão de container/12-factor).
    handler = logging.StreamHandler(sys.stdout)

    # Formatter: como cada log vira string?
    # JsonFormatter usa os mesmos placeholders do logging clássico
    # ("%(asctime)s", "%(levelname)s"...), mas cospe JSON em vez de texto.
    # Campos extras (request_id injetado pelo Filter, ou via extra={...})
    # entram automaticamente como chaves no JSON.
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
    )

    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    # Root logger: configurado uma vez, propaga pra todos os loggers filhos.
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Limpa handlers que uvicorn / FastAPI possam ter colocado antes,
    # senão vamos ver linha duplicada (texto + JSON).
    root.handlers.clear()
    root.addHandler(handler)