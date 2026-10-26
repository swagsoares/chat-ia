"""Regras de autenticação: cadastro, login e obtenção do usuário do token."""
from app.core.exceptions import CredenciaisInvalidasError, NaoAutenticadoError, UsuarioJaExisteError
from app.core.security import criar_token, gerar_hash_senha, verificar_senha
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import LoginEntrada, TokenSaida, UsuarioCriar, UsuarioSaida


class AuthService:
    def __init__(self, usuarios: UsuarioRepository):
        self.usuarios = usuarios

    def registrar(self, dados: UsuarioCriar) -> UsuarioSaida:
        if self.usuarios.buscar_por_username(dados.username):
            raise UsuarioJaExisteError("Este nome de usuário já está em uso.")
        criado = self.usuarios.criar(
            username=dados.username,
            nome=dados.nome.strip(),
            senha_hash=gerar_hash_senha(dados.senha),  # nunca guardamos a senha em texto puro
        )
        return UsuarioSaida(**criado)

    def login(self, dados: LoginEntrada) -> TokenSaida:
        usuario = self.usuarios.buscar_por_username(dados.username)
        # Mesma mensagem para usuário inexistente e senha errada (não revela qual dos dois)
        if not usuario or not verificar_senha(dados.senha, usuario["senha_hash"]):
            raise CredenciaisInvalidasError("Usuário ou senha incorretos.")
        token, expira = criar_token(usuario["id"], usuario["username"])
        return TokenSaida(access_token=token, expira_em_segundos=expira, usuario=UsuarioSaida(**usuario))

    def obter_usuario(self, usuario_id: int) -> UsuarioSaida:
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise NaoAutenticadoError("Usuário do token não existe mais.")
        return UsuarioSaida(**usuario)
