"""
conftest.py — configuração compartilhada de fixtures para todos os testes.

Utiliza um banco SQLite em memória com StaticPool para garantir que todas
as operações (create_all, sessões) compartilhem a mesma conexão.

IMPORTANTE: SQLite :memory: cria um banco novo por conexão por padrão.
O StaticPool força todas as conexões a reutilizar a mesma conexão subjacente,
garantindo que as tabelas criadas com create_all sejam visíveis para as sessões.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# IMPORTANTE: importar os models antes de criar as tabelas,
# para que a metadata do SQLAlchemy os conheça.
import app.models.registro  # noqa: F401

from app.main import app as fastapi_app
from app.db.base import Base
from app.db.session import get_db

# ---------------------------------------------------------------------------
# Engine SQLite em memória com StaticPool
# StaticPool: todas as chamadas a engine.connect() retornam a mesma conexão,
# garantindo que create_all e as queries das sessões vejam as mesmas tabelas.
# ---------------------------------------------------------------------------

engine_teste = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)


def override_get_db():
    """
    Substitui a dependência get_db por uma sessão apontando para o
    banco de dados em memória dos testes.
    """
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """
    Fixture executada automaticamente antes/após cada teste:
    - Cria todas as tabelas no banco em memória (StaticPool garante visibilidade)
    - Configura o override de dependência do FastAPI
    - Limpa tudo ao finalizar (tabelas removidas + override limpo)
    """
    # Cria as tabelas no engine de testes
    Base.metadata.create_all(bind=engine_teste)

    # Substitui get_db pelo banco de testes via injeção de dependência FastAPI
    fastapi_app.dependency_overrides[get_db] = override_get_db

    yield

    # Cleanup: remove as tabelas e restaura as dependências originais
    Base.metadata.drop_all(bind=engine_teste)
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def client():
    """TestClient do FastAPI pronto para uso nos testes."""
    return TestClient(fastapi_app)
