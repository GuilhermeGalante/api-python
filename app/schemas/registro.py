"""
Schemas Pydantic para o endpoint de registro de foco.
Seguindo SOLID-L: schemas de request e response separados.
Seguindo OWASP API3: nunca retorna o model ORM diretamente.
"""
import json
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class CategoriaEnum(str, Enum):
    """Categorias válidas para uma sessão de foco."""
    CODING = "coding"
    REUNIAO = "reuniao"
    ESTUDO = "estudo"
    OUTRO = "outro"


class RegistroFocoCreate(BaseModel):
    """
    Schema de entrada para criação de um registro de foco.
    Todas as validações de negócio são definidas aqui.
    """

    nivel_foco: int = Field(
        ...,
        ge=1,
        le=5,
        description="Nível de foco da sessão, de 1 (muito baixo) a 5 (excepcional)",
        json_schema_extra={"example": 4},
    )

    tempo_minutos: int = Field(
        ...,
        gt=0,
        le=480,
        description="Duração da sessão em minutos (máximo 8 horas = 480 min)",
        json_schema_extra={"example": 45},
    )

    comentario: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Descrição livre sobre a sessão",
        json_schema_extra={"example": "Implementei o módulo de autenticação sem interrupções"},
    )

    categoria: Optional[CategoriaEnum] = Field(
        default=None,
        description="Categoria da sessão: coding, reuniao, estudo ou outro",
    )

    tags: Optional[list[str]] = Field(
        default=None,
        max_length=10,
        description="Lista de tags descritivas (máximo 10, cada uma com no máximo 30 chars)",
    )

    data: Optional[datetime] = Field(
        default=None,
        description="Data/hora da sessão. Se não informada, usa o momento atual (UTC)",
    )

    @field_validator("comentario", mode="before")
    @classmethod
    def sanitizar_comentario(cls, v: str) -> str:
        """Remove espaços extras das extremidades do comentário (OWASP API10)."""
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validar_tags(cls, v: list[str] | None) -> list[str] | None:
        """Valida e sanitiza as tags."""
        if v is None:
            return v
        for tag in v:
            tag_stripped = tag.strip()
            if len(tag_stripped) > 30:
                raise ValueError(
                    f"A tag '{tag_stripped[:10]}...' excede o limite de 30 caracteres."
                )
        # Sanitiza e remove duplicatas mantendo a ordem
        seen = set()
        sanitized = []
        for tag in v:
            tag_clean = tag.strip()
            if tag_clean and tag_clean not in seen:
                seen.add(tag_clean)
                sanitized.append(tag_clean)
        return sanitized

    @model_validator(mode="after")
    def definir_data_padrao(self) -> "RegistroFocoCreate":
        """Se a data não for informada, define como o momento atual em UTC."""
        if self.data is None:
            self.data = datetime.now(timezone.utc)
        return self


class RegistroFocoResponse(BaseModel):
    """
    Schema de saída do registro de foco.
    Nunca expõe campos internos do ORM (OWASP API3).
    """

    id: str = Field(description="UUID único do registro")
    nivel_foco: int
    tempo_minutos: int
    comentario: str
    categoria: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    data: datetime
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, model) -> "RegistroFocoResponse":
        """
        Cria o schema de resposta a partir de um model ORM.
        Deserializa as tags do formato JSON armazenado no banco.
        """
        tags = []
        if model.tags_json:
            try:
                tags = json.loads(model.tags_json)
            except (json.JSONDecodeError, TypeError):
                tags = []

        return cls(
            id=model.id,
            nivel_foco=model.nivel_foco,
            tempo_minutos=model.tempo_minutos,
            comentario=model.comentario,
            categoria=model.categoria,
            tags=tags,
            data=model.data,
            created_at=model.created_at,
        )
