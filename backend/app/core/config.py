"""Configuração central da API.

Todas as variáveis vêm do arquivo .env (ou do ambiente). Nenhuma chave fica
escrita no código. Veja o .env.example para a lista documentada.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]  # pasta backend/
load_dotenv(BASE_DIR / ".env")


def _caminho_db() -> str:
    """Caminho relativo no .env é resolvido a partir da pasta backend/."""
    caminho = Path(os.getenv("DATABASE_PATH", "data/chat.db"))
    return str(caminho if caminho.is_absolute() else BASE_DIR / caminho)


def _int(nome: str, padrao: int) -> int:
    try:
        return int(os.getenv(nome, padrao))
    except ValueError:
        return padrao


@dataclass(frozen=True)
class Settings:
    app_nome: str = os.getenv("APP_NOME", "Chat IA Generativa — API")
    # Segurança / JWT
    jwt_secret: str = os.getenv("JWT_SECRET", "chave-padrao-de-desenvolvimento-troque-no-env")
    jwt_algoritmo: str = os.getenv("JWT_ALGORITMO", "HS256")
    jwt_expira_minutos: int = _int("JWT_EXPIRA_MINUTOS", 120)
    # Persistência
    database_path: str = _caminho_db()
    # Modelo de linguagem
    llm_provider: str = os.getenv("LLM_PROVIDER", "simulado").lower()
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    llm_timeout: int = _int("LLM_TIMEOUT", 30)
    # CORS (o front em Streamlit chama via requests no servidor, mas deixamos configurável)
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:8501")


settings = Settings()
