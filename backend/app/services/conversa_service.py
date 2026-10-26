"""Regras de conversas e mensagens.

- Toda operação recebe o usuário logado e só enxerga as conversas dele
  (conversa de outro usuário responde 404, sem revelar que existe).
- Ao enviar mensagem: monta o histórico, chama o provider do modelo e só
  então grava a pergunta e a resposta. Se o modelo falhar (503), nada é
  gravado e o usuário pode reenviar.
- A primeira mensagem vira o título da conversa.
"""
from app.core.exceptions import ConversaNaoEncontradaError
from app.llm.provider import LLMProvider
from app.repositories.conversa_repository import ConversaRepository
from app.repositories.mensagem_repository import MensagemRepository
from app.schemas.conversa import (
    ConversaCriar,
    ConversaDetalhe,
    ConversaResumo,
    MensagemEntrada,
    MensagemSaida,
    TrocaMensagemSaida,
)

TITULO_PADRAO = "Nova conversa"
TAMANHO_TITULO = 40


def _titulo_a_partir_de(texto: str) -> str:
    linha = " ".join(texto.split())
    return linha if len(linha) <= TAMANHO_TITULO else linha[: TAMANHO_TITULO - 1].rstrip() + "…"


class ConversaService:
    def __init__(self, conversas: ConversaRepository, mensagens: MensagemRepository, llm: LLMProvider):
        self.conversas = conversas
        self.mensagens = mensagens
        self.llm = llm

    # ---- consultas -------------------------------------------------------
    def listar(self, usuario_id: int) -> list[ConversaResumo]:
        return [ConversaResumo(**c) for c in self.conversas.listar_do_usuario(usuario_id)]

    def _obter_ou_404(self, conversa_id: int, usuario_id: int) -> dict:
        conversa = self.conversas.buscar_do_usuario(conversa_id, usuario_id)
        if not conversa:
            raise ConversaNaoEncontradaError(f"Conversa {conversa_id} não encontrada.")
        return conversa

    def abrir(self, conversa_id: int, usuario_id: int) -> ConversaDetalhe:
        conversa = self._obter_ou_404(conversa_id, usuario_id)
        mensagens = [MensagemSaida(**m) for m in self.mensagens.listar_da_conversa(conversa_id)]
        return ConversaDetalhe(
            id=conversa["id"],
            titulo=conversa["titulo"],
            criado_em=conversa["criado_em"],
            atualizado_em=conversa["atualizado_em"],
            mensagens=mensagens,
        )

    # ---- comandos --------------------------------------------------------
    def criar(self, usuario_id: int, dados: ConversaCriar) -> ConversaResumo:
        titulo = (dados.titulo or "").strip() or TITULO_PADRAO
        criada = self.conversas.criar(usuario_id, titulo)
        return ConversaResumo(**criada, total_mensagens=0)

    def excluir(self, conversa_id: int, usuario_id: int) -> None:
        if not self.conversas.excluir(conversa_id, usuario_id):
            raise ConversaNaoEncontradaError(f"Conversa {conversa_id} não encontrada.")

    def enviar_mensagem(self, conversa_id: int, usuario_id: int, dados: MensagemEntrada) -> TrocaMensagemSaida:
        conversa = self._obter_ou_404(conversa_id, usuario_id)
        historico = [
            {"papel": m["papel"], "conteudo": m["conteudo"]}
            for m in self.mensagens.listar_da_conversa(conversa_id)
        ]
        historico.append({"papel": "user", "conteudo": dados.conteudo})

        # Pode lançar LLMIndisponivelError -> 503 (nada foi gravado ainda)
        texto_resposta = self.llm.gerar_resposta(historico)

        msg_usuario = self.mensagens.criar(conversa_id, "user", dados.conteudo)
        msg_bot = self.mensagens.criar(conversa_id, "assistant", texto_resposta, modelo=self.llm.nome_modelo)

        titulo = conversa["titulo"]
        if titulo == TITULO_PADRAO and len(historico) == 1:
            titulo = _titulo_a_partir_de(dados.conteudo)
            self.conversas.atualizar_titulo(conversa_id, titulo)
        self.conversas.tocar(conversa_id)

        return TrocaMensagemSaida(
            conversa_id=conversa_id,
            titulo=titulo,
            mensagem_usuario=MensagemSaida(**msg_usuario),
            resposta=MensagemSaida(**msg_bot),
            modelo=self.llm.nome_modelo,
            criado_em=msg_bot["criado_em"],
        )
