"""
Model ORM do registro de foco — representa a tabela `registros_foco` no banco.
Utiliza UUID como chave primária (OWASP API1 — nunca expõe IDs sequenciais).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class RegistroFoco(Base):
    """
    Entidade que representa uma sessão de trabalho/estudo com nível de foco.
    A coluna `tags` armazena as tags como JSON serializado (string).
    """

    __tablename__ = "registros_foco"

    # UUID como PK — mitiga BOLA (Broken Object Level Authorization)
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Nível de foco de 1 a 5
    nivel_foco: Mapped[int] = mapped_column(Integer, nullable=False)

    # Duração da sessão em minutos (1 a 480)
    tempo_minutos: Mapped[int] = mapped_column(Integer, nullable=False)

    # Comentário livre sobre a sessão
    comentario: Mapped[str] = mapped_column(Text, nullable=False)

    # Categoria da sessão (opcional)
    categoria: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Tags serializadas como JSON (ex: '["backend", "auth"]')
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True, default="[]")

    # Data/hora da sessão (pode ser informada ou preenchida automaticamente)
    data: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Data/hora de criação do registro (gerada automaticamente)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
