"""
Testes do endpoint POST /api/v1/registro-foco.
Os fixtures de banco de dados e client são fornecidos pelo conftest.py.
"""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Dados base válidos para reutilização nos testes
# ---------------------------------------------------------------------------

PAYLOAD_VALIDO = {
    "nivel_foco": 4,
    "tempo_minutos": 45,
    "comentario": "Implementei o módulo de autenticação sem interrupções",
    "categoria": "coding",
    "tags": ["backend", "auth"],
    "data": "2025-06-10T14:30:00",
}


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

class TestCriarRegistroFoco:
    """Testes para o endpoint POST /api/v1/registro-foco."""

    def test_criacao_com_dados_validos_retorna_201(self, client):
        """✅ Criação com dados válidos deve retornar 201 com os dados corretos."""
        resposta = client.post("/api/v1/registro-foco", json=PAYLOAD_VALIDO)

        assert resposta.status_code == 201

        dados = resposta.json()
        assert "id" in dados
        assert len(dados["id"]) == 36  # UUID formato padrão
        assert dados["nivel_foco"] == 4
        assert dados["tempo_minutos"] == 45
        assert dados["comentario"] == "Implementei o módulo de autenticação sem interrupções"
        assert dados["categoria"] == "coding"
        assert dados["tags"] == ["backend", "auth"]
        assert "data" in dados
        assert "created_at" in dados

    def test_nivel_foco_zero_retorna_422(self, client):
        """✅ nivel_foco = 0 deve retornar 422 (abaixo do mínimo permitido de 1)."""
        payload = {**PAYLOAD_VALIDO, "nivel_foco": 0}
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 422

    def test_nivel_foco_seis_retorna_422(self, client):
        """✅ nivel_foco = 6 deve retornar 422 (acima do máximo permitido de 5)."""
        payload = {**PAYLOAD_VALIDO, "nivel_foco": 6}
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 422

    def test_tempo_minutos_zero_retorna_422(self, client):
        """✅ tempo_minutos = 0 deve retornar 422 (deve ser maior que zero)."""
        payload = {**PAYLOAD_VALIDO, "tempo_minutos": 0}
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 422

    def test_tempo_minutos_acima_do_limite_retorna_422(self, client):
        """✅ tempo_minutos = 481 deve retornar 422 (máximo é 480 = 8 horas)."""
        payload = {**PAYLOAD_VALIDO, "tempo_minutos": 481}
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 422

    def test_comentario_vazio_retorna_422(self, client):
        """✅ comentario vazio deve retornar 422 (mínimo de 3 caracteres)."""
        payload = {**PAYLOAD_VALIDO, "comentario": ""}
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 422

    def test_comentario_muito_curto_retorna_422(self, client):
        """comentario com menos de 3 chars deve retornar 422."""
        payload = {**PAYLOAD_VALIDO, "comentario": "ab"}
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 422

    def test_criacao_sem_campos_opcionais(self, client):
        """Criação apenas com campos obrigatórios deve retornar 201."""
        payload = {
            "nivel_foco": 3,
            "tempo_minutos": 30,
            "comentario": "Sessão de estudos simples",
        }
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 201

        dados = resposta.json()
        assert dados["categoria"] is None
        assert dados["tags"] == []

    def test_id_e_uuid_nao_inteiro(self, client):
        """O ID retornado deve ser um UUID, não um inteiro sequencial (OWASP API1)."""
        resposta = client.post("/api/v1/registro-foco", json=PAYLOAD_VALIDO)
        dados = resposta.json()

        # Verifica formato UUID (8-4-4-4-12 caracteres)
        partes = dados["id"].split("-")
        assert len(partes) == 5
        assert [len(p) for p in partes] == [8, 4, 4, 4, 12]

    def test_tags_com_mais_de_10_elementos_retorna_422(self, client):
        """Lista de tags com mais de 10 elementos deve retornar 422."""
        payload = {
            **PAYLOAD_VALIDO,
            "tags": [f"tag{i}" for i in range(11)],
        }
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 422

    def test_categoria_invalida_retorna_422(self, client):
        """Categoria que não é um dos valores permitidos deve retornar 422."""
        payload = {**PAYLOAD_VALIDO, "categoria": "invalida"}
        resposta = client.post("/api/v1/registro-foco", json=payload)
        assert resposta.status_code == 422
