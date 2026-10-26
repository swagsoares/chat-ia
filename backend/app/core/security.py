"""Funções de segurança: hash de senha (bcrypt) e token JWT.

- Senhas NUNCA são gravadas em texto puro: guardamos apenas o hash bcrypt.
- O token é um JWT assinado (HS256) com o id do usuário no campo "sub" e
  data de expiração no campo "exp".
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


class TokenInvalidoError(Exception):
    """Token ausente, malformado, com assinatura inválida ou expirado."""


def gerar_hash_senha(senha: str) -> str:
    # bcrypt considera no máximo 72 bytes; o schema já limita o tamanho da senha
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        return False


def criar_token(usuario_id: int, username: str) -> tuple[str, int]:
    """Retorna (token, segundos_ate_expirar)."""
    agora = datetime.now(timezone.utc)
    expira_em = agora + timedelta(minutes=settings.jwt_expira_minutos)
    payload = {
        "sub": str(usuario_id),
        "username": username,
        "iat": agora,
        "exp": expira_em,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algoritmo)
    return token, settings.jwt_expira_minutos * 60


def decodificar_token(token: str) -> int:
    """Valida o token e devolve o id do usuário. Lança TokenInvalidoError."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algoritmo])
        return int(payload["sub"])
    except jwt.ExpiredSignatureError as exc:
        raise TokenInvalidoError("Sessão expirada. Faça login novamente.") from exc
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise TokenInvalidoError("Token inválido.") from exc
