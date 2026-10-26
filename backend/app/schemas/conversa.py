from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ConversaCriar(BaseModel):
    """Entrada de POST /conversas. O título é opcional: se vier vazio, vira
    "Nova conversa" e é trocado automaticamente pela primeira mensagem."""

    titulo: str | None = Field(default=None, max_length=80, examples=["Dúvidas sobre FastAPI"])


class ConversaResumo(BaseModel):
    """Item da lista de conversas (barra lateral)."""

    id: int
    titulo: str
    criado_em: str
    atualizado_em: str
    total_mensagens: int = 0


class MensagemSaida(BaseModel):
    id: int
    papel: Literal["user", "assistant"]
    conteudo: str
    modelo: str | None = None
    criado_em: str


class ConversaDetalhe(BaseModel):
    """Conversa aberta, com o histórico completo."""

    id: int
    titulo: str
    criado_em: str
    atualizado_em: str
    mensagens: list[MensagemSaida]


class MensagemEntrada(BaseModel):
    """Entrada de POST /conversas/{id}/mensagens."""

    conteudo: str = Field(
        ..., min_length=1, max_length=4000,
        description="Texto enviado pelo usuário", examples=["Me explique o que é uma API REST"],
    )

    @field_validator("conteudo")
    @classmethod
    def nao_pode_ser_so_espacos(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("A mensagem não pode ser vazia.")
        return valor


class TrocaMensagemSaida(BaseModel):
    """Resposta de POST /conversas/{id}/mensagens (mensagem do usuário + resposta do bot)."""

    conversa_id: int
    titulo: str
    mensagem_usuario: MensagemSaida
    resposta: MensagemSaida
    modelo: str
    criado_em: str
