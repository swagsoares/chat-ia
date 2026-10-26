"""Estado mínimo da sessão do Streamlit.

Guardamos SÓ: token, dados básicos do usuário e o id da conversa ativa.
O histórico de mensagens NUNCA fica aqui — é sempre lido da API.
"""
import streamlit as st

from services.api_client import ApiClient

CHAVES = {"token": None, "usuario": None, "conversa_ativa_id": None}


def init_state() -> None:
    for chave, padrao in CHAVES.items():
        st.session_state.setdefault(chave, padrao)


def esta_logado() -> bool:
    return bool(st.session_state.get("token"))


def logar(token: str, usuario: dict) -> None:
    st.session_state.token = token
    st.session_state.usuario = {"id": usuario["id"], "nome": usuario["nome"], "username": usuario["username"]}
    st.session_state.conversa_ativa_id = None


def deslogar() -> None:
    for chave, padrao in CHAVES.items():
        st.session_state[chave] = padrao


def usuario() -> dict | None:
    return st.session_state.get("usuario")


def conversa_ativa() -> int | None:
    return st.session_state.get("conversa_ativa_id")


def definir_conversa_ativa(conversa_id: int | None) -> None:
    st.session_state.conversa_ativa_id = conversa_id


def api() -> ApiClient:
    """Cliente da API já com o token da sessão."""
    return ApiClient(token=st.session_state.get("token"))
