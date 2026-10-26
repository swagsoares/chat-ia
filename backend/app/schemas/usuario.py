from pydantic import BaseModel, ConfigDict, Field


class UsuarioCriar(BaseModel):
    """Entrada de POST /auth/registro."""

    username: str = Field(
        ..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9_.-]+$",
        description="Login único (letras, números, _ . -)", examples=["vitor"],
    )
    nome: str = Field(..., min_length=2, max_length=80, description="Nome de exibição", examples=["Vitor Soares"])
    senha: str = Field(..., min_length=6, max_length=72, description="Mínimo de 6 caracteres", examples=["senha123"])


class LoginEntrada(BaseModel):
    """Entrada de POST /auth/login."""

    username: str = Field(..., min_length=1, max_length=30, examples=["vitor"])
    senha: str = Field(..., min_length=1, max_length=72, examples=["senha123"])


class UsuarioSaida(BaseModel):
    """Dados públicos do usuário (nunca inclui o hash da senha)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    nome: str
    criado_em: str


class TokenSaida(BaseModel):
    """Resposta do login."""

    access_token: str
    token_type: str = "bearer"
    expira_em_segundos: int
    usuario: UsuarioSaida
