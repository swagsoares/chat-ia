"""Caixa de envio de mensagem (st.chat_input)."""
import streamlit as st

LIMITE_CARACTERES = 4000  # mesmo limite validado pelo Pydantic na API


def render_caixa_envio(desabilitada: bool = False) -> str | None:
    texto = st.chat_input(
        "Digite sua mensagem…", max_chars=LIMITE_CARACTERES, disabled=desabilitada, key="caixa_envio"
    )
    return texto.strip() if texto and texto.strip() else None
