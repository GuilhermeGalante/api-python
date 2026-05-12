"""
Repository de RegistroFoco — camada de acesso a dados.
Encapsula todas as queries ao banco de dados, isolando a lógica de persistência
dos serviços de negócio (Repository Pattern, SOLID-S).
"""
import json
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.models.registro import RegistroFoco
from app.schemas.registro import RegistroFocoCreate, CategoriaEnum


class RegistroRepository:
    """
    Repositório responsável por todas as operações de banco de dados
    relacionadas à entidade RegistroFoco.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def criar(self, dados: RegistroFocoCreate) -> RegistroFoco:
        """
        Persiste um novo registro de foco no banco de dados.
        Serializa as tags como JSON para armazenamento em coluna Text.
        """
        # Serializa as tags para JSON (armazenamento em coluna Text)
        tags_json = json.dumps(dados.tags or [], ensure_ascii=False)

        registro = RegistroFoco(
            id=str(uuid.uuid4()),
            nivel_foco=dados.nivel_foco,
            tempo_minutos=dados.tempo_minutos,
            comentario=dados.comentario,
            categoria=dados.categoria.value if dados.categoria else None,
            tags_json=tags_json,
            data=dados.data,
        )

        self.db.add(registro)
        self.db.commit()
        self.db.refresh(registro)
        return registro

    def buscar_com_filtros(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        categoria: Optional[CategoriaEnum] = None,
    ) -> list[RegistroFoco]:
        """
        Retorna registros filtrados por período e/ou categoria.
        Todos os filtros são opcionais.
        """
        stmt = select(RegistroFoco)

        if data_inicio:
            stmt = stmt.where(RegistroFoco.data >= data_inicio)

        if data_fim:
            stmt = stmt.where(RegistroFoco.data <= data_fim)

        if categoria:
            stmt = stmt.where(RegistroFoco.categoria == categoria.value)

        # Ordena do mais recente para o mais antigo
        stmt = stmt.order_by(RegistroFoco.data.desc())

        return list(self.db.execute(stmt).scalars().all())

    def contar_total(self) -> int:
        """Retorna o número total de registros na base."""
        return self.db.execute(select(func.count(RegistroFoco.id))).scalar_one()
