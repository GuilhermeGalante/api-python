"""
Serviço de registro de foco — contém as regras de negócio para criação de sessões.
Orquestra a validação de negócio e a persistência via repositório (SOLID-S e D).
"""
from sqlalchemy.orm import Session

from app.repositories.registro_repository import RegistroRepository
from app.schemas.registro import RegistroFocoCreate, RegistroFocoResponse


class RegistroService:
    """
    Serviço responsável pelas regras de negócio do registro de foco.
    Recebe o repositório via injeção de dependência (SOLID-D).
    """

    def __init__(self, repository: RegistroRepository) -> None:
        self.repository = repository

    def criar_registro(self, dados: RegistroFocoCreate) -> RegistroFocoResponse:
        """
        Cria um novo registro de foco aplicando as regras de negócio.
        As validações de formato já foram realizadas pelo schema Pydantic.
        Aqui ficam as regras de negócio adicionais (se houver).
        """
        # Aqui podem ser adicionadas regras de negócio futuras, por exemplo:
        # - Verificar se já existe uma sessão ativa no mesmo horário
        # - Limitar número de registros por dia
        # - Aplicar gamificação (streaks, badges)

        modelo_orm = self.repository.criar(dados)
        return RegistroFocoResponse.from_orm_model(modelo_orm)


def get_registro_service(db: Session) -> RegistroService:
    """
    Factory function para criação do serviço com suas dependências.
    Utilizada como dependência FastAPI para inversão de controle (SOLID-D).
    """
    repository = RegistroRepository(db)
    return RegistroService(repository)
