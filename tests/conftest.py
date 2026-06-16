"""
Fixtures compartilhadas dos testes de integração.

O pytest descobre este arquivo automaticamente — todas as fixtures
ficam disponíveis em qualquer teste da pasta `tests/` sem import.

Pipeline de uma fixture:
    [SETUP] → yield → [TEARDOWN]

Estratégia de banco:
    - Usamos o Postgres de TESTE (porta 5433, tmpfs).
    - A cada teste, criamos e dropamos todas as tabelas → isolamento total.
    - Override de `get_db` faz a rota usar a sessão de teste em vez da de prod.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app


# ============================================================
# ENGINE — conexão com o Postgres de teste (porta 5433).
# Criada UMA vez por rodada (scope="session") porque conexão
# é cara — abrir/fechar a cada teste seria muito lento.
# ============================================================
@pytest.fixture(scope="session")
def engine_teste():
    """Engine SQLAlchemy apontando para o Postgres de teste."""
    engine = create_engine(settings.database_url_test)
    yield engine
    engine.dispose()


# ============================================================
# DB_SESSION — uma sessão (transação) NOVA por teste.
# Cria todas as tabelas antes, dropa todas depois.
# Garante isolamento absoluto: nada vaza entre testes.
# ============================================================
@pytest.fixture(scope="function")
def db_session(engine_teste) -> Session:
    """Sessão SQLAlchemy isolada por teste."""
    # SETUP: cria todas as tabelas no Postgres de teste.
    Base.metadata.create_all(bind=engine_teste)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine_teste,
    )
    sessao = TestingSessionLocal()

    try:
        yield sessao
    finally:
        # TEARDOWN: fecha sessão e DROPA todas as tabelas.
        # Próximo teste vai encontrar banco totalmente limpo.
        sessao.close()
        Base.metadata.drop_all(bind=engine_teste)


# ============================================================
# CLIENT — TestClient do FastAPI com override do get_db.
# A rota acha que está usando o banco de prod (Depends(get_db)),
# mas na verdade está usando a `db_session` de teste.
# ============================================================
@pytest.fixture(scope="function")
def client(db_session) -> TestClient:
    """TestClient do FastAPI usando o banco de teste."""

    def get_db_override():
        """Substitui get_db: devolve a sessão de teste em vez da de prod."""
        try:
            yield db_session
        finally:
            pass  # Cleanup é feito pela fixture db_session

    # Intercepta o Depends(get_db) nas rotas.
    app.dependency_overrides[get_db] = get_db_override

    with TestClient(app) as test_client:
        yield test_client

    # Limpa o override pra não vazar pra outros testes.
    app.dependency_overrides.clear()