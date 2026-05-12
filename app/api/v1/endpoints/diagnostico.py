"""
Endpoint GET /api/v1/diagnostico-produtividade — retorna diagnóstico de produtividade.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.db.session import get_db
from app.schemas.diagnostico import DiagnosticoResponse
from app.schemas.registro import CategoriaEnum
from app.services.diagnostico_service import get_diagnostico_service, DiagnosticoService

router = APIRouter()


@router.get(
    "/diagnostico-produtividade",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_200_OK,
    summary="Obter diagnóstico de produtividade",
    description=(
        "Retorna um diagnóstico completo de produtividade com base nos registros de foco. "
        "Inclui média de foco, tempo total, distribuição por nível, categoria mais produtiva "
        "e feedback inteligente baseado na média calculada."
    ),
    responses={
        200: {"description": "Diagnóstico gerado com sucesso"},
        400: {"description": "data_inicio é posterior a data_fim"},
        404: {"description": "Nenhum registro encontrado para os filtros informados"},
        401: {"description": "API Key inválida ou ausente"},
        429: {"description": "Rate limit excedido"},
    },
    dependencies=[Depends(verify_api_key)],
)
async def obter_diagnostico_produtividade(
    data_inicio: Optional[datetime] = Query(
        default=None,
        description="Filtrar registros a partir desta data (ISO 8601)",
        examples=["2025-06-01T00:00:00"],
    ),
    data_fim: Optional[datetime] = Query(
        default=None,
        description="Filtrar registros até esta data (ISO 8601)",
        examples=["2025-06-30T23:59:59"],
    ),
    categoria: Optional[CategoriaEnum] = Query(
        default=None,
        description="Filtrar por categoria: coding, reuniao, estudo ou outro",
    ),
    db: Session = Depends(get_db),
) -> DiagnosticoResponse:
    """
    Gera diagnóstico de produtividade com base nos registros filtrados.

    **Filtros opcionais:**
    - **data_inicio**: filtra registros a partir desta data
    - **data_fim**: filtra registros até esta data
    - **categoria**: filtra por categoria específica

    **Retorno:**
    - Métricas agregadas (total, média, tempo total)
    - Distribuição de foco por nível (1-5)
    - Categoria mais produtiva
    - Sessão mais longa
    - Feedback inteligente (crítico/baixo/médio/alto)
    - Período analisado
    """
    # Valida que data_inicio não é posterior a data_fim
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O parâmetro 'data_inicio' não pode ser posterior ao 'data_fim'.",
        )

    service: DiagnosticoService = get_diagnostico_service(db)

    # Busca registros com os filtros informados
    registros = service.repository.buscar_com_filtros(data_inicio, data_fim, categoria)

    if not registros:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Nenhum registro de foco encontrado para os filtros informados. "
                "Registre suas primeiras sessões usando o endpoint POST /api/v1/registro-foco."
            ),
        )

    return service.gerar_diagnostico(data_inicio, data_fim, categoria)
