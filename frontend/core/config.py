"""Configuração do front. A URL da API vem do .env (API_URL) — nunca fica fixa no código."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

API_URL: str = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
API_TIMEOUT: float = float(os.getenv("API_TIMEOUT", "30"))
