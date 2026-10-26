"""Acesso à tabela usuarios. Só SQL aqui — nenhuma regra de negócio."""
import sqlite3

from app.utils import agora_iso


class UsuarioRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def buscar_por_username(self, username: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM usuarios WHERE lower(username) = lower(?)", (username,)
        ).fetchone()
        return dict(row) if row else None

    def buscar_por_id(self, usuario_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
        return dict(row) if row else None

    def criar(self, username: str, nome: str, senha_hash: str) -> dict:
        cur = self.conn.execute(
            "INSERT INTO usuarios (username, nome, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
            (username, nome, senha_hash, agora_iso()),
        )
        self.conn.commit()
        return self.buscar_por_id(cur.lastrowid)
