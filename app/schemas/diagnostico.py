"""
Schemas Pydantic para o endpoint de diagnóstico de produtividade.
Representa a estrutura de resposta do diagnóstico com todos os sub-schemas.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SessaoMaisLonga(BaseModel):
    """Informações sobre a sessão de maior duração no período analisado."""
    tempo_minutos: int
    nivel_foco: int
    categoria: Optional[str] = None


class Feedback(BaseModel):
    """Feedback gerado pelo DiagnosticoService baseado na média de foco."""
    nivel: str = Field(description="crítico | baixo | médio | alto")
    titulo: str
    descricao: str
    sugestoes: list[str]


class PeriodoAnalisado(BaseModel):
    """Intervalo de tempo que abrange os registros analisados."""
    inicio: datetime
    fim: datetime


class DiagnosticoResponse(BaseModel):
    """
    Schema completo de resposta do endpoint de diagnóstico de produtividade.
    Agrega métricas, feedback inteligente e dados do período analisado.
    """

    total_registros: int = Field(description="Número total de sessões no período")
    media_foco: float = Field(description="Média aritmética do nível de foco")
    tempo_total_minutos: int = Field(description="Soma total de minutos de foco")
    tempo_total_formatado: str = Field(
        description="Tempo total formatado em horas e minutos (ex: '6h 20min')"
    )
    distribuicao_foco: dict[str, int] = Field(
        description="Contagem de sessões por nível de foco (chaves '1' a '5')"
    )
    categoria_mais_produtiva: Optional[str] = Field(
        default=None,
        description="Categoria com maior soma de tempo de foco",
    )
    sessao_mais_longa: Optional[SessaoMaisLonga] = Field(
        default=None,
        description="Dados da sessão com maior duração",
    )
    feedback: Feedback = Field(description="Diagnóstico inteligente baseado na média de foco")
    periodo_analisado: PeriodoAnalisado = Field(
        description="Intervalo de datas dos registros analisados"
    )
