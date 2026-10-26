"""Único ponto de acesso ao modelo de linguagem.

Trocar de modelo = mudar LLM_PROVIDER no .env. Rotas, serviços e front-end
não mudam, porque todos dependem só da interface LLMProvider.

Opções:
- simulado (padrão): respostas geradas por regras, sem internet nem chave.
- gemini: API gratuita do Google Gemini (precisa de GEMINI_API_KEY).
- offline: provider que está sempre indisponível — serve para demonstrar o 503.
"""
import random
import re
import unicodedata
from abc import ABC, abstractmethod
from functools import lru_cache

import requests

from app.core.config import settings
from app.core.exceptions import LLMIndisponivelError

# Histórico no formato [{"papel": "user"|"assistant", "conteudo": "..."}]
Historico = list[dict]


class LLMProvider(ABC):
    nome_provedor: str = "base"
    nome_modelo: str = "base"

    @abstractmethod
    def gerar_resposta(self, historico: Historico) -> str:
        """Recebe o histórico completo (a última mensagem é a do usuário) e
        devolve o texto da resposta. Lança LLMIndisponivelError se falhar."""

    def disponivel(self) -> bool:
        return True


# --------------------------------------------------------------------------- #
# 1) Simulado — respostas por regra
# --------------------------------------------------------------------------- #
def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower().strip()


class SimuladoProvider(LLMProvider):
    nome_provedor = "simulado"
    nome_modelo = "simulado-regras-v1"

    GLOSSARIO = {
        "api rest": "Uma **API REST** é uma interface que expõe recursos (como /conversas) por URLs "
                    "e usa os verbos HTTP — GET para ler, POST para criar, PUT/PATCH para alterar e "
                    "DELETE para remover. As respostas costumam vir em JSON e cada requisição é "
                    "independente (stateless).",
        "fastapi": "**FastAPI** é um framework Python para construir APIs. Ele usa type hints e "
                   "Pydantic para validar entradas e saídas e gera a documentação em /docs automaticamente.",
        "jwt": "**JWT** (JSON Web Token) é um token assinado que carrega informações como o id do "
               "usuário e a data de expiração. A API confere a assinatura a cada requisição, sem "
               "precisar guardar sessão.",
        "pydantic": "**Pydantic** valida dados a partir de classes Python. No FastAPI, se o corpo da "
                    "requisição não bater com o schema, a API responde 422 sozinha.",
        "streamlit": "**Streamlit** transforma scripts Python em apps web. A cada interação o script "
                     "roda de novo, e o st.session_state guarda o que precisa sobreviver entre execuções.",
        "token": "Um **token** é uma credencial que o cliente envia em cada requisição "
                 "(aqui no header Authorization: Bearer) para provar quem é.",
        "sqlite": "**SQLite** é um banco de dados relacional que fica num único arquivo. É ótimo para "
                  "projetos pequenos porque não precisa de servidor separado.",
    }

    SAUDACOES = ("oi", "ola", "bom dia", "boa tarde", "boa noite", "hey", "e ai", "salve")

    def gerar_resposta(self, historico: Historico) -> str:
        pergunta = historico[-1]["conteudo"] if historico else ""
        p = _normalizar(pergunta)
        turno = sum(1 for m in historico if m["papel"] == "user")

        if any(re.search(rf"\b{s}\b", p) for s in self.SAUDACOES) and len(p) < 40:
            return random.choice([
                "Olá! Sou o assistente simulado deste projeto. Pergunte algo como "
                "\"o que é uma API REST?\" ou \"o que é JWT?\".",
                "Oi! Tudo certo? Estou aqui para responder — sou um bot de regras, mas faço o meu melhor.",
            ])

        if "ajuda" in p or "o que voce faz" in p or "quem e voce" in p:
            return ("Sou um **bot simulado**: respondo com regras, sem modelo de linguagem de verdade. "
                    "Conheço alguns termos: " + ", ".join(sorted(self.GLOSSARIO)) + ". "
                    "Para usar o Gemini, basta definir LLM_PROVIDER=gemini no .env da API.")

        for termo, explicacao in self.GLOSSARIO.items():
            if termo in p:
                return explicacao

        if "obrigad" in p or "valeu" in p:
            return "De nada! Se quiser, abra uma nova conversa pela barra lateral."

        if p.endswith("?"):
            return random.choice([
                f"Boa pergunta! Como sou um bot simulado, não sei responder \"{pergunta.strip()}\" com "
                "precisão, mas a mensagem foi salva no histórico desta conversa.",
                f"Sobre \"{pergunta.strip()}\": eu sou só um bot de regras. Tente perguntar sobre "
                "API REST, FastAPI, JWT, Pydantic, Streamlit ou SQLite.",
            ])

        return (f"Recebi sua mensagem ({len(pergunta)} caracteres). Esta é a mensagem nº {turno} "
                f"desta conversa. Você disse: \"{pergunta.strip()}\"")


# --------------------------------------------------------------------------- #
# 2) Gemini — API gratuita do Google
# --------------------------------------------------------------------------- #
class GeminiProvider(LLMProvider):
    nome_provedor = "gemini"
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

    def __init__(self, api_key: str, modelo: str, timeout: int):
        self.api_key = api_key
        self.nome_modelo = modelo
        self.timeout = timeout

    def disponivel(self) -> bool:
        return bool(self.api_key)

    def gerar_resposta(self, historico: Historico) -> str:
        if not self.api_key:
            raise LLMIndisponivelError(
                "O modelo Gemini não está configurado (GEMINI_API_KEY vazia). Tente novamente mais tarde."
            )
        corpo = {
            "contents": [
                {"role": "model" if m["papel"] == "assistant" else "user", "parts": [{"text": m["conteudo"]}]}
                for m in historico[-20:]  # limita o contexto enviado
            ]
        }
        try:
            resp = requests.post(
                self.URL.format(modelo=self.nome_modelo),
                headers={"x-goog-api-key": self.api_key, "Content-Type": "application/json"},
                json=corpo,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise LLMIndisponivelError("Não foi possível falar com o Gemini agora. Tente novamente.") from exc

        if resp.status_code == 429:
            raise LLMIndisponivelError("Limite gratuito do Gemini atingido. Aguarde um pouco e tente de novo.")
        if resp.status_code >= 400:
            raise LLMIndisponivelError(f"O Gemini respondeu com erro ({resp.status_code}). Tente novamente.")

        try:
            partes = resp.json()["candidates"][0]["content"]["parts"]
            texto = "".join(p.get("text", "") for p in partes).strip()
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMIndisponivelError("O Gemini devolveu uma resposta vazia ou bloqueada.") from exc
        if not texto:
            raise LLMIndisponivelError("O Gemini devolveu uma resposta vazia.")
        return texto


# --------------------------------------------------------------------------- #
# 3) Offline — sempre indisponível (para demonstrar o tratamento do 503)
# --------------------------------------------------------------------------- #
class OfflineProvider(LLMProvider):
    nome_provedor = "offline"
    nome_modelo = "nenhum"

    def disponivel(self) -> bool:
        return False

    def gerar_resposta(self, historico: Historico) -> str:
        raise LLMIndisponivelError("O modelo de linguagem está fora do ar no momento. Tente novamente mais tarde.")


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Fábrica escolhida pelo .env. Também é usada como dependência do FastAPI."""
    escolha = settings.llm_provider
    if escolha == "gemini":
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.llm_timeout)
    if escolha == "offline":
        return OfflineProvider()
    return SimuladoProvider()
