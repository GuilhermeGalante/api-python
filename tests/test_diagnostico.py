"""
Testes do endpoint GET /api/v1/diagnostico-produtividade.
Os fixtures de banco de dados e client são fornecidos pelo conftest.py.
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helper para popular o banco de dados nos testes
# ---------------------------------------------------------------------------

def criar_registro(client, nivel_foco: int, tempo_minutos: int = 30,
                   categoria: str = "coding", data: str = "2025-06-10T10:00:00"):
    """Cria um registro de foco via API e retorna o response."""
    return client.post("/api/v1/registro-foco", json={
        "nivel_foco": nivel_foco,
        "tempo_minutos": tempo_minutos,
        "comentario": f"Sessão de teste com foco {nivel_foco}",
        "categoria": categoria,
        "data": data,
    })


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

class TestDiagnosticoSemRegistros:
    """Testes quando não há registros no banco."""

    def test_sem_registros_retorna_404(self, client):
        """✅ Sem registros → 404 com mensagem clara."""
        resposta = client.get("/api/v1/diagnostico-produtividade")

        assert resposta.status_code == 404
        dados = resposta.json()
        assert "detail" in dados
        assert len(dados["detail"]) > 0  # Mensagem não vazia

    def test_sem_registros_mensagem_em_portugues(self, client):
        """A mensagem de erro deve estar em português."""
        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()
        # Verifica que a mensagem orienta o usuário
        assert "registro" in dados["detail"].lower()


class TestDiagnosticoComRegistros:
    """Testes quando há registros no banco."""

    def test_com_registros_retorna_200(self, client):
        """✅ Com registros → 200 e campos corretos."""
        criar_registro(client, nivel_foco=4)
        criar_registro(client, nivel_foco=3)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        assert resposta.status_code == 200

    def test_campos_obrigatorios_presentes(self, client):
        """✅ Com registros → todos os campos esperados devem estar presentes."""
        criar_registro(client, nivel_foco=4)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        campos_obrigatorios = [
            "total_registros",
            "media_foco",
            "tempo_total_minutos",
            "tempo_total_formatado",
            "distribuicao_foco",
            "feedback",
            "periodo_analisado",
        ]
        for campo in campos_obrigatorios:
            assert campo in dados, f"Campo '{campo}' ausente na resposta"

    def test_total_registros_correto(self, client):
        """O total de registros deve refletir os registros criados."""
        criar_registro(client, nivel_foco=3)
        criar_registro(client, nivel_foco=5)
        criar_registro(client, nivel_foco=2)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        assert dados["total_registros"] == 3

    def test_media_foco_calculada_corretamente(self, client):
        """A média de foco deve ser a média aritmética dos registros."""
        criar_registro(client, nivel_foco=2)
        criar_registro(client, nivel_foco=4)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        assert dados["media_foco"] == 3.0

    def test_tempo_total_somado_corretamente(self, client):
        """O tempo total deve ser a soma de todos os tempos."""
        criar_registro(client, nivel_foco=4, tempo_minutos=30)
        criar_registro(client, nivel_foco=3, tempo_minutos=45)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        assert dados["tempo_total_minutos"] == 75

    def test_distribuicao_foco_com_chaves_1_a_5(self, client):
        """A distribuição de foco deve ter chaves de '1' a '5'."""
        criar_registro(client, nivel_foco=3)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        distribuicao = dados["distribuicao_foco"]
        for nivel in ["1", "2", "3", "4", "5"]:
            assert nivel in distribuicao


class TestFeedbackPorFaixaDeFoco:
    """✅ Testes da lógica de feedback para cada faixa de média de foco."""

    def test_feedback_critico_media_abaixo_de_2(self, client):
        """✅ Média < 2 → feedback nível 'crítico'."""
        # média = 1.0 (abaixo de 2)
        criar_registro(client, nivel_foco=1)
        criar_registro(client, nivel_foco=1)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        assert dados["feedback"]["nivel"] == "crítico"
        assert len(dados["feedback"]["sugestoes"]) > 0

    def test_feedback_baixo_media_entre_2_e_3(self, client):
        """✅ Média entre 2 e 3 → feedback nível 'baixo'."""
        # média = 2.5 (entre 2 e 3)
        criar_registro(client, nivel_foco=2)
        criar_registro(client, nivel_foco=3)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        assert dados["feedback"]["nivel"] == "baixo"
        assert len(dados["feedback"]["sugestoes"]) > 0

    def test_feedback_medio_media_entre_3_e_4(self, client):
        """✅ Média entre 3 e 4 → feedback nível 'médio'."""
        # média = 3.5 (entre 3 e 4)
        criar_registro(client, nivel_foco=3)
        criar_registro(client, nivel_foco=4)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        assert dados["feedback"]["nivel"] == "médio"
        assert len(dados["feedback"]["sugestoes"]) > 0

    def test_feedback_alto_media_acima_de_4(self, client):
        """✅ Média > 4 → feedback nível 'alto'."""
        # média = 5.0 (acima de 4)
        criar_registro(client, nivel_foco=5)
        criar_registro(client, nivel_foco=5)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        dados = resposta.json()

        assert dados["feedback"]["nivel"] == "alto"
        assert len(dados["feedback"]["sugestoes"]) > 0

    def test_feedback_tem_titulo_e_descricao(self, client):
        """Todos os feedbacks devem ter título e descrição não vazios."""
        criar_registro(client, nivel_foco=4)

        resposta = client.get("/api/v1/diagnostico-produtividade")
        feedback = resposta.json()["feedback"]

        assert len(feedback["titulo"]) > 0
        assert len(feedback["descricao"]) > 0


class TestFiltrosPorData:
    """✅ Testes dos filtros de data no diagnóstico."""

    def test_filtro_por_data_inicio(self, client):
        """✅ Filtro por data_inicio deve excluir registros anteriores."""
        # Registros em datas diferentes
        criar_registro(client, nivel_foco=5, data="2025-01-10T10:00:00")
        criar_registro(client, nivel_foco=2, data="2025-06-10T10:00:00")

        # Filtra apenas a partir de junho
        resposta = client.get(
            "/api/v1/diagnostico-produtividade",
            params={"data_inicio": "2025-06-01T00:00:00"},
        )
        dados = resposta.json()

        # Só deve retornar o registro de junho (nivel_foco=2)
        assert dados["total_registros"] == 1
        assert dados["media_foco"] == 2.0

    def test_filtro_por_data_fim(self, client):
        """Filtro por data_fim deve excluir registros posteriores."""
        criar_registro(client, nivel_foco=5, data="2025-01-10T10:00:00")
        criar_registro(client, nivel_foco=2, data="2025-06-10T10:00:00")

        # Filtra apenas até março
        resposta = client.get(
            "/api/v1/diagnostico-produtividade",
            params={"data_fim": "2025-03-31T23:59:59"},
        )
        dados = resposta.json()

        assert dados["total_registros"] == 1
        assert dados["media_foco"] == 5.0

    def test_data_inicio_posterior_a_data_fim_retorna_400(self, client):
        """✅ data_inicio > data_fim deve retornar 400."""
        resposta = client.get(
            "/api/v1/diagnostico-produtividade",
            params={
                "data_inicio": "2025-12-31T00:00:00",
                "data_fim": "2025-01-01T00:00:00",
            },
        )
        assert resposta.status_code == 400


class TestFiltrosPorCategoria:
    """Testes dos filtros de categoria no diagnóstico."""

    def test_filtro_por_categoria(self, client):
        """Filtro por categoria deve retornar apenas os registros daquela categoria."""
        criar_registro(client, nivel_foco=5, categoria="coding")
        criar_registro(client, nivel_foco=2, categoria="reuniao")
        criar_registro(client, nivel_foco=4, categoria="coding")

        resposta = client.get(
            "/api/v1/diagnostico-produtividade",
            params={"categoria": "coding"},
        )
        dados = resposta.json()

        assert dados["total_registros"] == 2

    def test_filtro_por_categoria_sem_resultados_retorna_404(self, client):
        """Filtro por categoria sem registros deve retornar 404."""
        criar_registro(client, nivel_foco=3, categoria="coding")

        resposta = client.get(
            "/api/v1/diagnostico-produtividade",
            params={"categoria": "reuniao"},
        )
        assert resposta.status_code == 404
