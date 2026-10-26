"""Rotas de conversas. Todas são protegidas: o Depends(get_usuario_atual) exige
o token e entrega o usuário logado, e o serviço só acessa as conversas dele."""
from fastapi import APIRouter, Depends, Path, Response, status

from app.core.deps import get_conversa_service, get_usuario_atual
from app.schemas.comum import RESPOSTA_401, RESPOSTA_404, RESPOSTA_503
from app.schemas.conversa import (
    ConversaCriar,
    ConversaDetalhe,
    ConversaResumo,
    MensagemEntrada,
    TrocaMensagemSaida,
)
from app.schemas.usuario import UsuarioSaida
from app.services.conversa_service import ConversaService

router = APIRouter(prefix="/conversas", tags=["Conversas"], responses=RESPOSTA_401)

IdConversa = Path(..., ge=1, description="Id da conversa")


@router.get(
    "",
    response_model=list[ConversaResumo],
    summary="Lista as conversas do usuário logado",
    description="Devolve as conversas do usuário, da mais recente para a mais antiga "
                "(usado na barra lateral do front).",
)
def listar(
    usuario: UsuarioSaida = Depends(get_usuario_atual),
    service: ConversaService = Depends(get_conversa_service),
) -> list[ConversaResumo]:
    return service.listar(usuario.id)


@router.post(
    "",
    response_model=ConversaResumo,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova conversa",
    description="Cria uma conversa vazia. Se o título não for enviado, ela começa como "
                "\"Nova conversa\" e recebe o texto da primeira mensagem como título.",
)
def criar(
    dados: ConversaCriar | None = None,
    usuario: UsuarioSaida = Depends(get_usuario_atual),
    service: ConversaService = Depends(get_conversa_service),
) -> ConversaResumo:
    return service.criar(usuario.id, dados or ConversaCriar())


@router.get(
    "/{conversa_id}",
    response_model=ConversaDetalhe,
    summary="Abre uma conversa com o histórico",
    description="Devolve a conversa e todas as mensagens, em ordem. Conversas de outros "
                "usuários respondem 404.",
    responses=RESPOSTA_404,
)
def abrir(
    conversa_id: int = IdConversa,
    usuario: UsuarioSaida = Depends(get_usuario_atual),
    service: ConversaService = Depends(get_conversa_service),
) -> ConversaDetalhe:
    return service.abrir(conversa_id, usuario.id)


@router.delete(
    "/{conversa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui uma conversa",
    description="Remove a conversa e todas as mensagens dela.",
    responses=RESPOSTA_404,
)
def excluir(
    conversa_id: int = IdConversa,
    usuario: UsuarioSaida = Depends(get_usuario_atual),
    service: ConversaService = Depends(get_conversa_service),
) -> Response:
    service.excluir(conversa_id, usuario.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversa_id}/mensagens",
    response_model=TrocaMensagemSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Envia uma mensagem e recebe a resposta do bot",
    description="Grava a mensagem do usuário e a resposta do modelo de linguagem configurado. "
                "Se o modelo estiver indisponível, responde **503** e nada é gravado.",
    responses={**RESPOSTA_404, **RESPOSTA_503},
)
def enviar_mensagem(
    dados: MensagemEntrada,
    conversa_id: int = IdConversa,
    usuario: UsuarioSaida = Depends(get_usuario_atual),
    service: ConversaService = Depends(get_conversa_service),
) -> TrocaMensagemSaida:
    return service.enviar_mensagem(conversa_id, usuario.id, dados)
