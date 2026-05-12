"""
Base declarativa do SQLAlchemy — todos os models ORM herdam desta classe.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base para todos os models ORM da aplicação."""
    pass
