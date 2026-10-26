"""Exibição das mensagens do chat (st.chat_message)."""
import streamlit as st

AVATARES = {"user": ":material/person:", "assistant": ":material/smart_toy:"}


def render_mensagem(papel: str, conteudo: str, modelo: str | None = None) -> None:
    with st.chat_message(papel, avatar=AVATARES.get(papel)):
        st.markdown(conteudo)
        if papel == "assistant" and modelo:
            st.caption(f"modelo: {modelo}")


def render_mensagens(mensagens: list[dict]) -> None:
    for m in mensagens:
        render_mensagem(m["papel"], m["conteudo"], m.get("modelo"))
