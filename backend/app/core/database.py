"""Conexão com o SQLite e criação das tabelas.

O banco é um arquivo em disco (DATABASE_PATH), então os dados sobrevivem
ao reinício da API.
"""
import sqlite3
from pathlib import Path
from typing import Iterator

from app.core.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    NOT NULL UNIQUE,
    nome        TEXT    NOT NULL,
    senha_hash  TEXT    NOT NULL,
    criado_em   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS conversas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo         TEXT    NOT NULL,
    criado_em      TEXT    NOT NULL,
    atualizado_em  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS mensagens (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    conversa_id  INTEGER NOT NULL REFERENCES conversas(id) ON DELETE CASCADE,
    papel        TEXT    NOT NULL CHECK (papel IN ('user', 'assistant')),
    conteudo     TEXT    NOT NULL,
    modelo       TEXT,
    criado_em    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conversas_usuario ON conversas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_mensagens_conversa ON mensagens(conversa_id);
"""


def _conectar() -> sqlite3.Connection:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with _conectar() as conn:
        conn.executescript(SCHEMA)


def get_conexao() -> Iterator[sqlite3.Connection]:
    """Dependência do FastAPI: abre uma conexão por requisição e fecha no fim."""
    conn = _conectar()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
