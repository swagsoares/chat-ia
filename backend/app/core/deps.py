"""Dependências injetadas nas rotas (Depends).

- get_conexao: conexão SQLite por requisição.
- get_usuario_atual: lê o header Authorization: Bearer <token>, valida o JWT e
  devolve o usuário logado. Sem token ou com token inválido -> 401.
- get_*_service: monta os serviços com seus repositórios e o provider do modelo.
"""
import sqlite3

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import get_conexao
from app.core.exceptions import NaoAutenticadoError
from app.core.security import TokenInvalidoError, decodificar_token
from app.llm.provider import LLMProvider, get_llm_provider
from app.repositories.conversa_repository import ConversaRepository
from app.repositories.mensagem_repository import MensagemRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioSaida
from app.services.auth_service import AuthService
from app.services.conversa_service import ConversaService

# auto_error=False para devolvermos 401 (e não 403) com mensagem própria
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Cole aqui o access_token retornado por POST /auth/login",
)


def get_auth_service(conn: sqlite3.Connection = Depends(get_conexao)) -> AuthService:
    return AuthService(UsuarioRepository(conn))


def get_conversa_service(
    conn: sqlite3.Connection = Depends(get_conexao),
    llm: LLMProvider = Depends(get_llm_provider),
) -> ConversaService:
    return ConversaService(ConversaRepository(conn), MensagemRepository(conn), llm)


def get_usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> UsuarioSaida:
    if credenciais is None or credenciais.scheme.lower() != "bearer":
        raise NaoAutenticadoError("Token não informado. Envie Authorization: Bearer <token>.")
    try:
        usuario_id = decodificar_token(credenciais.credentials)
    except TokenInvalidoError as exc:
        raise NaoAutenticadoError(str(exc)) from exc
    return auth_service.obter_usuario(usuario_id)
