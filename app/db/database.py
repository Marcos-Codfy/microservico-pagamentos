"""
Configuração da conexão com o Postgres via SQLAlchemy.

Este módulo define cinco peças fundamentais:

1. `engine`     — a "tomada de luz" do banco. Criada UMA vez, no import.
2. `SessionLocal` — fábrica de sessions. Cada request HTTP cria sua session.
3. `Base`       — classe-mãe de todos os modelos ORM (PagamentoDB etc.).
4. `get_db`     — gerador usado com FastAPI Depends() pra injetar a session
                  na rota e fechá-la automaticamente no fim.
5. `ping_db`    — smoke test pra health check profundo (Aula 4).

Princípio aplicado: separação de infraestrutura e domínio.
Este arquivo é puramente técnico — não sabe NADA de pagamento, juros,
regras de negócio. Só sabe falar com Postgres.

A engine deste módulo aponta para o banco de PRODUÇÃO local (porta 5432).
A engine de teste será criada na Sessão 3, em uma fixture do pytest, e
vai apontar para `settings.database_url_test` (porta 5433).
"""
import logging
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


logger = logging.getLogger(__name__)


# Engine: a conexão de baixo nível com o Postgres de PROD (porta 5432).
# Criada uma vez quando este módulo é importado pela primeira vez.
# - `echo=False`: não loga todo SQL gerado. Mude pra True pra debug.
# - `pool_pre_ping=True`: testa a conexão antes de usar (evita erro
#   "connection has been closed" depois que o container reinicia).
engine = create_engine(
    settings.database_url_prod,
    echo=False,
    pool_pre_ping=True,
)

# SessionLocal: fábrica de sessions.
# Cada `SessionLocal()` produz uma session nova e isolada.
# - `autoflush=False`: a session não envia mudanças automaticamente —
#   só quando chamamos `.commit()` ou `.flush()`.
# - `autocommit=False`: precisamos chamar `.commit()` explicitamente.
#   Isso nos dá controle sobre transações (tudo ou nada).
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """
    Classe-base de todos os modelos ORM do projeto.

    Todo modelo (PagamentoDB, ClienteDB, etc.) vai herdar dessa classe.
    O SQLAlchemy usa essa herança pra descobrir quais tabelas existem
    e gerar o SQL de criação delas.

    Sintaxe SQLAlchemy 2.0 (moderna). Em projetos antigos você vai ver
    `declarative_base()` (função) — versão legada do mesmo conceito.
    """
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Gerador (generator) que fornece uma session do banco e garante
    que ela seja fechada ao final do uso.

    Uso com FastAPI:
        @router.post("/")
        def criar_pagamento(db: Session = Depends(get_db)):
            # db já está pronta pra usar
            ...

    O FastAPI vai:
    1. Chamar get_db() → recebe o `db` (até o `yield`).
    2. Injetar `db` na rota.
    3. Quando a rota termina, retoma `get_db()` após o yield,
       executando o `db.close()` no `finally`.

    Por que generator (yield) em vez de função normal (return)?
    Porque precisamos executar CÓDIGO DEPOIS que a rota termina
    (o `close()`). Função normal retorna e morre — generator pausa,
    espera, e retoma.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ping_db() -> bool:
    """
    Smoke test de conectividade com o Postgres.

    Executa `SELECT 1` — a query mais barata possível, sem tocar em
    nenhuma tabela. Serve pro endpoint /health saber se o banco está
    acessível AGORA (não no startup — agora mesmo, neste instante).

    Returns:
        True  → banco respondeu, conexão viva.
        False → qualquer exceção (conexão recusada, timeout, credencial
                inválida, banco caído). Erro fica no log; a função
                NÃO propaga a exceção pra não crashar o /health.

    Por que engolir a exceção:
        Health check é INFORMATIVO, não CORRETIVO. Ele reporta o estado
        em forma de bool — quem decide o status code HTTP é o /health.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as erro:
        logger.warning("health.db.ping_falhou", extra={"motivo": str(erro)})
        return False