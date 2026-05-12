"""
Configuração da sessão do banco de dados SQLAlchemy.
Fornece a dependência `get_db` para injeção via FastAPI Depends().
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import get_settings

# Obtém a URL de conexão das configurações
settings = get_settings()

# Cria o engine SQLAlchemy
# check_same_thread=False é necessário para SQLite com FastAPI (múltiplas threads)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug,  # Loga as queries SQL no modo debug
)

# Factory de sessões — cada requisição recebe sua própria sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependência FastAPI que fornece uma sessão de banco de dados.
    Garante que a sessão seja fechada ao final de cada requisição,
    mesmo em caso de erro (uso de try/finally).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
