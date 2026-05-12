"""
Serviço de diagnóstico de produtividade.
Implementa o Strategy Pattern para as regras de feedback, permitindo extensão
sem modificar o núcleo do serviço (SOLID-O — Open/Closed Principle).
"""
from datetime import datetime
from typing import Optional, Protocol
from collections import defaultdict

from app.models.registro import RegistroFoco
from app.repositories.registro_repository import RegistroRepository
from app.schemas.diagnostico import (
    DiagnosticoResponse,
    Feedback,
    PeriodoAnalisado,
    SessaoMaisLonga,
)
from app.schemas.registro import CategoriaEnum
from sqlalchemy.orm import Session


# ---------------------------------------------------------------------------
# Strategy Pattern — cada estratégia define um nível de feedback
# Para adicionar um novo nível, basta criar uma nova classe e adicioná-la
# à lista `ESTRATEGIAS_FEEDBACK` sem modificar o DiagnosticoService.
# ---------------------------------------------------------------------------

class FeedbackStrategy(Protocol):
    """
    Protocolo (interface) para estratégias de feedback.
    SOLID-I: Interface segregation — contrato mínimo e focado.
    """

    def aplicavel(self, media_foco: float) -> bool:
        """Retorna True se esta estratégia é aplicável para a média informada."""
        ...

    def gerar_feedback(self) -> Feedback:
        """Gera e retorna o feedback para o nível correspondente."""
        ...


class FeedbackCritico:
    """Estratégia de feedback para média de foco abaixo de 2."""

    def aplicavel(self, media_foco: float) -> bool:
        return media_foco < 2

    def gerar_feedback(self) -> Feedback:
        return Feedback(
            nivel="crítico",
            titulo="Atenção: produtividade em risco 🔴",
            descricao=(
                "Sua média de foco está muito baixa. Isso pode indicar distrações excessivas, "
                "cansaço acumulado ou ambiente inadequado para trabalho focado."
            ),
            sugestoes=[
                "Faça pausas longas e descansadas entre as sessões",
                "Identifique e elimine as principais fontes de distração",
                "Revise o ambiente de trabalho (ruído, iluminação, ergonomia)",
                "Considere dormir mais e reduzir a carga de trabalho por alguns dias",
            ],
        )


class FeedbackBaixo:
    """Estratégia de feedback para média de foco entre 2 e 3."""

    def aplicavel(self, media_foco: float) -> bool:
        return 2 <= media_foco < 3

    def gerar_feedback(self) -> Feedback:
        return Feedback(
            nivel="baixo",
            titulo="Abaixo do potencial 🟡",
            descricao=(
                "Você está trabalhando, mas o nível de foco pode melhorar bastante. "
                "Com alguns ajustes simples de rotina, você pode subir significativamente."
            ),
            sugestoes=[
                "Experimente a técnica Pomodoro (25 min foco + 5 min pausa)",
                "Silencie todas as notificações durante as sessões de trabalho",
                "Defina metas claras e específicas antes de iniciar cada sessão",
                "Evite multitarefas — escolha uma única tarefa por sessão",
            ],
        )


class FeedbackMedio:
    """Estratégia de feedback para média de foco entre 3 e 4."""

    def aplicavel(self, media_foco: float) -> bool:
        return 3 <= media_foco < 4

    def gerar_feedback(self) -> Feedback:
        return Feedback(
            nivel="médio",
            titulo="No caminho certo 🟢",
            descricao=(
                "Sua produtividade está em um bom nível! Você está consistente. "
                "Foque agora em identificar o que já está funcionando e amplificar esses fatores."
            ),
            sugestoes=[
                "Tente aumentar a duração das sessões longas progressivamente",
                "Identifique seu horário de pico de energia e reserve para tarefas difíceis",
                "Reduza as sessões curtas e fragmentadas",
                "Documente o que funcionou bem em cada sessão produtiva",
            ],
        )


class FeedbackAlto:
    """Estratégia de feedback para média de foco acima de 4."""

    def aplicavel(self, media_foco: float) -> bool:
        return media_foco >= 4

    def gerar_feedback(self) -> Feedback:
        return Feedback(
            nivel="alto",
            titulo="Maratona produtiva de alto nível! 🚀",
            descricao=(
                "Sua média de foco está acima de 4 — excelente desempenho! "
                "Continue mantendo sessões focadas e respeite os intervalos para sustentar esse ritmo."
            ),
            sugestoes=[
                "Continue com sessões de 45-90 minutos que estão funcionando",
                "Mantenha o ritual de início de sessão que está gerando resultados",
                "Respeite os descansos — a consistência a longo prazo depende disso",
                "Documente e compartilhe seu método para solidificá-lo como hábito",
            ],
        )


# Lista de estratégias em ordem de prioridade (da mais específica para a mais geral)
# Para adicionar um novo nível de feedback, basta adicionar uma nova instância aqui
ESTRATEGIAS_FEEDBACK: list[FeedbackStrategy] = [
    FeedbackCritico(),
    FeedbackBaixo(),
    FeedbackMedio(),
    FeedbackAlto(),
]


# ---------------------------------------------------------------------------
# Serviço principal de diagnóstico
# ---------------------------------------------------------------------------

class DiagnosticoService:
    """
    Serviço que calcula e retorna o diagnóstico completo de produtividade.
    Utiliza o Strategy Pattern para o feedback, garantindo extensibilidade (SOLID-O).
    """

    def __init__(self, repository: RegistroRepository) -> None:
        self.repository = repository
        self.estrategias = ESTRATEGIAS_FEEDBACK

    def gerar_diagnostico(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        categoria: Optional[CategoriaEnum] = None,
    ) -> DiagnosticoResponse:
        """
        Gera o diagnóstico completo de produtividade com base nos registros filtrados.
        """
        registros = self.repository.buscar_com_filtros(data_inicio, data_fim, categoria)

        total = len(registros)

        # Calcula a média ponderada de foco
        media_foco = round(sum(r.nivel_foco for r in registros) / total, 2)

        # Soma total de minutos
        tempo_total = sum(r.tempo_minutos for r in registros)

        # Formata o tempo total em horas e minutos
        horas = tempo_total // 60
        minutos = tempo_total % 60
        if horas > 0 and minutos > 0:
            tempo_formatado = f"{horas}h {minutos}min"
        elif horas > 0:
            tempo_formatado = f"{horas}h"
        else:
            tempo_formatado = f"{minutos}min"

        # Distribuição de foco: contagem por nível (1 a 5)
        distribuicao: dict[str, int] = {str(i): 0 for i in range(1, 6)}
        for r in registros:
            distribuicao[str(r.nivel_foco)] += 1

        # Categoria mais produtiva: a que acumula mais tempo
        tempo_por_categoria: dict[str, int] = defaultdict(int)
        for r in registros:
            if r.categoria:
                tempo_por_categoria[r.categoria] += r.tempo_minutos
        categoria_mais_produtiva = (
            max(tempo_por_categoria, key=lambda k: tempo_por_categoria[k])
            if tempo_por_categoria
            else None
        )

        # Sessão mais longa
        sessao_mais_longa_orm = max(registros, key=lambda r: r.tempo_minutos)
        sessao_mais_longa = SessaoMaisLonga(
            tempo_minutos=sessao_mais_longa_orm.tempo_minutos,
            nivel_foco=sessao_mais_longa_orm.nivel_foco,
            categoria=sessao_mais_longa_orm.categoria,
        )

        # Período analisado: do registro mais antigo ao mais recente
        datas = [r.data for r in registros]
        periodo = PeriodoAnalisado(
            inicio=min(datas),
            fim=max(datas),
        )

        # Seleciona o feedback pela estratégia aplicável
        feedback = self._selecionar_feedback(media_foco)

        return DiagnosticoResponse(
            total_registros=total,
            media_foco=media_foco,
            tempo_total_minutos=tempo_total,
            tempo_total_formatado=tempo_formatado,
            distribuicao_foco=distribuicao,
            categoria_mais_produtiva=categoria_mais_produtiva,
            sessao_mais_longa=sessao_mais_longa,
            feedback=feedback,
            periodo_analisado=periodo,
        )

    def _selecionar_feedback(self, media_foco: float) -> Feedback:
        """
        Percorre as estratégias de feedback e retorna a primeira que for aplicável.
        Por padrão, retorna o feedback de nível alto (fallback seguro).
        """
        for estrategia in self.estrategias:
            if estrategia.aplicavel(media_foco):
                return estrategia.gerar_feedback()

        # Fallback — não deve ocorrer se as estratégias cobrirem todos os ranges
        return FeedbackAlto().gerar_feedback()


def get_diagnostico_service(db: Session) -> DiagnosticoService:
    """
    Factory function para criação do serviço com suas dependências.
    Utilizada como dependência FastAPI para inversão de controle (SOLID-D).
    """
    repository = RegistroRepository(db)
    return DiagnosticoService(repository)
