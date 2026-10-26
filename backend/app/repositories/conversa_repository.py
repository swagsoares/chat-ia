"""Acesso à tabela conversas.

Toda consulta filtra por usuario_id: é aqui que garantimos, no nível dos
dados, que um usuário nunca enxerga a conversa de outro (autorização).
"""
import sqlite3

from app.utils import agora_iso


class ConversaRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def listar_do_usuario(self, usuario_id: int) -> list[dict]:
        rows = self.conn.execute(
            """
            SELECT c.id, c.titulo, c.criado_em, c.atualizado_em,
                   COUNT(m.id) AS total_mensagens
              FROM conversas c
              LEFT JOIN mensagens m ON m.conversa_id = c.id
             WHERE c.usuario_id = ?
             GROUP BY c.id
             ORDER BY c.atualizado_em DESC, c.id DESC
            """,
            (usuario_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def buscar_do_usuario(self, conversa_id: int, usuario_id: int) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM conversas WHERE id = ? AND usuario_id = ?",
            (conversa_id, usuario_id),
        ).fetchone()
        return dict(row) if row else None

    def criar(self, usuario_id: int, titulo: str) -> dict:
        agora = agora_iso()
        cur = self.conn.execute(
            "INSERT INTO conversas (usuario_id, titulo, criado_em, atualizado_em) VALUES (?, ?, ?, ?)",
            (usuario_id, titulo, agora, agora),
        )
        self.conn.commit()
        return self.buscar_do_usuario(cur.lastrowid, usuario_id)

    def atualizar_titulo(self, conversa_id: int, titulo: str) -> None:
        self.conn.execute("UPDATE conversas SET titulo = ? WHERE id = ?", (titulo, conversa_id))
        self.conn.commit()

    def tocar(self, conversa_id: int) -> None:
        """Atualiza o atualizado_em (a conversa sobe para o topo da lista)."""
        self.conn.execute(
            "UPDATE conversas SET atualizado_em = ? WHERE id = ?", (agora_iso(), conversa_id)
        )
        self.conn.commit()

    def excluir(self, conversa_id: int, usuario_id: int) -> bool:
        cur = self.conn.execute(
            "DELETE FROM conversas WHERE id = ? AND usuario_id = ?", (conversa_id, usuario_id)
        )
        self.conn.commit()
        return cur.rowcount > 0
