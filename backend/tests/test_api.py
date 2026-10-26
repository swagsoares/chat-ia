"""Testes da API. Rodar dentro de backend/:  pytest -v

Usa um banco SQLite temporário, então não mexe nos seus dados.
"""
import os
import tempfile

import pytest

# Precisa vir ANTES de importar a app: aponta o banco para um arquivo temporário
_TMP = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(_TMP, "teste.db")
os.environ["LLM_PROVIDER"] = "simulado"
os.environ["JWT_SECRET"] = "chave-de-teste-com-mais-de-32-bytes-ok"

from fastapi.testclient import TestClient  # noqa: E402

from app.llm.provider import OfflineProvider, get_llm_provider  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _criar_e_logar(client, username: str) -> dict:
    client.post("/auth/registro", json={"username": username, "nome": username.title(), "senha": "senha123"})
    r = client.post("/auth/login", json={"username": username, "senha": "senha123"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_health_publico(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["provedor"] == "simulado"


def test_registro_e_login(client):
    r = client.post("/auth/registro", json={"username": "ana", "nome": "Ana", "senha": "senha123"})
    assert r.status_code == 201
    assert "senha" not in r.text and "hash" not in r.text  # nunca devolve senha/hash

    assert client.post("/auth/registro", json={"username": "ana", "nome": "Ana", "senha": "x123456"}).status_code == 409
    assert client.post("/auth/login", json={"username": "ana", "senha": "errada"}).status_code == 401

    r = client.post("/auth/login", json={"username": "ana", "senha": "senha123"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"


def test_senha_guardada_com_hash():
    import sqlite3
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    hash_salvo = conn.execute("SELECT senha_hash FROM usuarios WHERE username='ana'").fetchone()[0]
    conn.close()
    assert hash_salvo != "senha123" and hash_salvo.startswith("$2")  # bcrypt


def test_rotas_protegidas_exigem_token(client):
    assert client.get("/conversas").status_code == 401
    assert client.post("/conversas").status_code == 401
    assert client.get("/conversas", headers={"Authorization": "Bearer token-falso"}).status_code == 401
    assert client.get("/auth/me").status_code == 401


def test_fluxo_completo_de_conversas(client):
    h = _criar_e_logar(client, "bruno")

    r = client.post("/conversas", headers=h)
    assert r.status_code == 201
    conversa_id = r.json()["id"]
    assert r.json()["titulo"] == "Nova conversa"

    r = client.post(f"/conversas/{conversa_id}/mensagens", headers=h,
                    json={"conteudo": "Me explique o que é uma API REST"})
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["mensagem_usuario"]["papel"] == "user"
    assert corpo["resposta"]["papel"] == "assistant"
    assert "API REST" in corpo["resposta"]["conteudo"]
    assert corpo["titulo"].startswith("Me explique")  # 1ª mensagem vira título

    client.post("/conversas", headers=h)  # segunda conversa
    lista = client.get("/conversas", headers=h).json()
    assert len(lista) == 2

    r = client.get(f"/conversas/{conversa_id}", headers=h)
    assert r.status_code == 200
    assert [m["papel"] for m in r.json()["mensagens"]] == ["user", "assistant"]


def test_404_conversa_inexistente(client):
    h = _criar_e_logar(client, "carla")
    assert client.get("/conversas/99999", headers=h).status_code == 404
    assert client.post("/conversas/99999/mensagens", headers=h, json={"conteudo": "oi"}).status_code == 404


def test_usuario_nao_ve_conversa_de_outro(client):
    h_dono = _criar_e_logar(client, "dono")
    h_intruso = _criar_e_logar(client, "intruso")
    conversa_id = client.post("/conversas", headers=h_dono).json()["id"]

    assert client.get(f"/conversas/{conversa_id}", headers=h_intruso).status_code == 404
    assert client.post(f"/conversas/{conversa_id}/mensagens", headers=h_intruso,
                       json={"conteudo": "oi"}).status_code == 404
    assert client.delete(f"/conversas/{conversa_id}", headers=h_intruso).status_code == 404
    assert all(c["id"] != conversa_id for c in client.get("/conversas", headers=h_intruso).json())


def test_422_requisicao_invalida(client):
    h = _criar_e_logar(client, "davi")
    conversa_id = client.post("/conversas", headers=h).json()["id"]
    assert client.post(f"/conversas/{conversa_id}/mensagens", headers=h, json={}).status_code == 422
    r = client.post(f"/conversas/{conversa_id}/mensagens", headers=h, json={"conteudo": "   "})
    assert r.status_code == 422
    assert "detail" in r.json()
    assert client.post("/auth/registro", json={"username": "x", "nome": "X", "senha": "1"}).status_code == 422


def test_503_modelo_indisponivel_nao_grava_nada(client):
    h = _criar_e_logar(client, "eva")
    conversa_id = client.post("/conversas", headers=h).json()["id"]

    app.dependency_overrides[get_llm_provider] = lambda: OfflineProvider()
    try:
        r = client.post(f"/conversas/{conversa_id}/mensagens", headers=h, json={"conteudo": "oi"})
        assert r.status_code == 503
        assert "detail" in r.json()
    finally:
        app.dependency_overrides.clear()

    assert client.get(f"/conversas/{conversa_id}", headers=h).json()["mensagens"] == []


def test_excluir_conversa(client):
    h = _criar_e_logar(client, "fabio")
    conversa_id = client.post("/conversas", headers=h).json()["id"]
    assert client.delete(f"/conversas/{conversa_id}", headers=h).status_code == 204
    assert client.get(f"/conversas/{conversa_id}", headers=h).status_code == 404


def test_dados_sobrevivem_ao_reinicio():
    """Sobe uma NOVA instância da app (simula reinício) e confere que os dados continuam."""
    with TestClient(app) as novo_client:
        h = _criar_e_logar(novo_client, "bruno")  # usuário criado no teste anterior
        conversas = novo_client.get("/conversas", headers=h).json()
        assert len(conversas) == 2
        assert any(c["total_mensagens"] == 2 for c in conversas)
