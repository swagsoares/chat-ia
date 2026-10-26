from fastapi import APIRouter, Depends, status

from app.core.deps import get_auth_service, get_usuario_atual
from app.schemas.comum import RESPOSTA_401, ErroSaida
from app.schemas.usuario import LoginEntrada, TokenSaida, UsuarioCriar, UsuarioSaida
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/registro",
    response_model=UsuarioSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma conta",
    description="Cadastra um novo usuário. A senha é guardada apenas como hash bcrypt.",
    responses={409: {"model": ErroSaida, "description": "Nome de usuário já em uso"}},
)
def registrar(dados: UsuarioCriar, service: AuthService = Depends(get_auth_service)) -> UsuarioSaida:
    return service.registrar(dados)


@router.post(
    "/login",
    response_model=TokenSaida,
    summary="Faz login e devolve o token",
    description="Confere usuário e senha e devolve um **JWT**. Envie-o nas rotas protegidas no "
                "header `Authorization: Bearer <token>` (no /docs, use o botão **Authorize**).",
    responses={401: {"model": ErroSaida, "description": "Usuário ou senha incorretos"}},
)
def login(dados: LoginEntrada, service: AuthService = Depends(get_auth_service)) -> TokenSaida:
    return service.login(dados)


@router.get(
    "/me",
    response_model=UsuarioSaida,
    summary="Dados do usuário logado",
    description="Rota protegida. Útil para o front validar se o token ainda é válido.",
    responses=RESPOSTA_401,
)
def me(usuario: UsuarioSaida = Depends(get_usuario_atual)) -> UsuarioSaida:
    return usuario
