"""Testes do provider do modelo (sem internet: a chamada HTTP é simulada)."""
import pytest

from app.core.exceptions import LLMIndisponivelError
from app.llm import provider as prov


class _RespostaFalsa:
    def __init__(self, status_code, corpo):
        self.status_code = status_code
        self._corpo = corpo

    def json(self):
        return self._corpo


HISTORICO = [
    {"papel": "user", "conteudo": "Oi"},
    {"papel": "assistant", "conteudo": "Olá!"},
    {"papel": "user", "conteudo": "O que é FastAPI?"},
]


def test_gemini_monta_historico_e_le_resposta(monkeypatch):
    enviado = {}

    def post_falso(url, headers, json, timeout):
        enviado.update(url=url, headers=headers, json=json)
        return _RespostaFalsa(200, {"candidates": [{"content": {"parts": [{"text": "Um framework."}]}}]})

    monkeypatch.setattr(prov.requests, "post", post_falso)
    g = prov.GeminiProvider(api_key="chave", modelo="gemini-2.5-flash", timeout=5)

    assert g.gerar_resposta(HISTORICO) == "Um framework."
    assert "gemini-2.5-flash:generateContent" in enviado["url"]
    assert enviado["headers"]["x-goog-api-key"] == "chave"
    assert [c["role"] for c in enviado["json"]["contents"]] == ["user", "model", "user"]


def test_gemini_sem_chave_fica_indisponivel():
    g = prov.GeminiProvider(api_key="", modelo="x", timeout=5)
    assert g.disponivel() is False
    with pytest.raises(LLMIndisponivelError):
        g.gerar_resposta(HISTORICO)


def test_gemini_limite_gratuito_vira_503(monkeypatch):
    monkeypatch.setattr(prov.requests, "post", lambda *a, **k: _RespostaFalsa(429, {}))
    g = prov.GeminiProvider(api_key="chave", modelo="x", timeout=5)
    with pytest.raises(LLMIndisponivelError, match="Limite"):
        g.gerar_resposta(HISTORICO)


def test_simulado_responde_glossario():
    assert "JWT" in prov.SimuladoProvider().gerar_resposta([{"papel": "user", "conteudo": "o que é jwt?"}])
