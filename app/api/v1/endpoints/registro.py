"""
Endpoint POST /api/v1/registro-foco — registra uma nova sessão de foco.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.registro import RegistroFocoCreate, RegistroFocoResponse
from app.services.registro_service import get_registro_service, RegistroService

router = APIRouter()


@router.post(
    "/registro-foco",
    response_model=RegistroFocoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar sessão de foco",
    description=(
        "Registra uma nova sessão de trabalho/estudo com nível de foco. "
        "Retorna o registro criado com UUID único."
    ),
    responses={
        201: {"description": "Registro criado com sucesso"},
        422: {"description": "Dados inválidos — validação falhou"},
        400: {"description": "Regra de negócio violada"},
        401: {"description": "API Key inválida ou ausente"},
        429: {"description": "Rate limit excedido"},
    },
    dependencies=[Depends(verify_api_key)],
)
async def criar_registro_foco(
    dados: RegistroFocoCreate,
    db: Session = Depends(get_db),
) -> RegistroFocoResponse:
    """
    Cria um novo registro de sessão de foco.

    - **nivel_foco**: de 1 (muito baixo) a 5 (excepcional) — obrigatório
    - **tempo_minutos**: duração em minutos, de 1 a 480 — obrigatório
    - **comentario**: descrição da sessão, 3 a 500 caracteres — obrigatório
    - **categoria**: `coding`, `reuniao`, `estudo` ou `outro` — opcional
    - **tags**: lista de tags (máx 10, cada uma com máx 30 chars) — opcional
    - **data**: data/hora da sessão em ISO 8601 (padrão: agora em UTC) — opcional
    """
    service: RegistroService = get_registro_service(db)
    return service.criar_registro(dados)
