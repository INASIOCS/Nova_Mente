"""Testes da API que não consomem quota da LLM."""

from __future__ import annotations

import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")
TestClient = fastapi_testclient.TestClient

from app.api.main import app  # noqa: E402

cliente = TestClient(app)


def test_raiz():
    r = cliente.get("/")
    assert r.status_code == 200
    assert r.json()["servico"] == "NovaMente"


def test_saude_reporta_backends():
    r = cliente.get("/saude")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["status"] == "ok"
    assert "storage_backend_ativo" in corpo
    assert "caminho_llm" in corpo
    # sem ?profundo, o healthcheck nao toca na rede: nada a afirmar sobre o bucket
    assert corpo["bucket_acessivel"] is None


def test_saude_profundo_checa_o_bucket(monkeypatch):
    """O teste nao pode depender do .env nem de credenciais do OCI."""
    from app.storage import factory
    from app.storage.local import LocalStorage

    monkeypatch.setattr(factory, "criar_storage", lambda *a, **k: (LocalStorage(), None))

    r = cliente.get("/saude", params={"profundo": "true"})
    assert r.status_code == 200
    corpo = r.json()
    # com o backend local o bucket e um diretorio, sempre disponivel
    assert corpo["bucket_acessivel"] is True
    assert corpo["storage_backend_ativo"] == "local"


def test_opcoes_lista_todos_os_eixos():
    r = cliente.get("/opcoes")
    assert r.status_code == 200
    corpo = r.json()
    assert "Iniciante" in corpo["perfil_destinatario"]
    assert "Flashcards" in corpo["formato_saida"]
    assert "Quiz" in corpo["formato_saida"]
    assert len(corpo["formato_saida"]) == 5
    assert "Geral" in corpo["nicho_setor"]


def test_adaptar_rejeita_payload_invalido():
    r = cliente.post("/adaptar", json={"documento_titulo": "x"})
    assert r.status_code == 422


def test_adaptar_rejeita_perfil_desconhecido():
    r = cliente.post(
        "/adaptar",
        json={
            "documento_titulo": "Documento de teste para validacao de schema",
            "documento_conteudo": "a" * 120,
            "perfil_destinatario": "Mestre Jedi",
            "formato_saida": "Flashcards",
        },
    )
    assert r.status_code == 422


def test_exportar_markdown_a_partir_de_resposta_valida():
    from tests.test_contrato import RESPOSTA_BRIEFING

    r = cliente.post("/exportar/markdown", json=RESPOSTA_BRIEFING)
    assert r.status_code == 200
    assert "Dominando Redes na Nuvem" in r.text
