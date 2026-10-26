"""Acesso à tabela mensagens."""
import sqlite3

from app.utils import agora_iso


class MensagemRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def listar_da_conversa(self, conversa_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, papel, conteudo, modelo, criado_em FROM mensagens "
            "WHERE conversa_id = ? ORDER BY id",
            (conversa_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def criar(self, conversa_id: int, papel: str, conteudo: str, modelo: str | None = None) -> dict:
        cur = self.conn.execute(
            "INSERT INTO mensagens (conversa_id, papel, conteudo, modelo, criado_em) VALUES (?, ?, ?, ?, ?)",
            (conversa_id, papel, conteudo, modelo, agora_iso()),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id, papel, conteudo, modelo, criado_em FROM mensagens WHERE id = ?",
            (cur.lastrowid,),
        ).fetchone()
        return dict(row)

    def excluir(self, mensagem_id: int) -> None:
        self.conn.execute("DELETE FROM mensagens WHERE id = ?", (mensagem_id,))
        self.conn.commit()
