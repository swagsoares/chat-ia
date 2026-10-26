"""Tela inicial de uma conversa nova, com sugestões de perguntas."""
import streamlit as st

SUGESTOES = [
    "Me explique o que é uma API REST",
    "O que é JWT?",
    "Para que serve o Pydantic?",
    "O que você sabe fazer?",
]


def render_boas_vindas(nome: str) -> str | None:
    """Mostra a saudação e devolve a sugestão clicada (ou None)."""
    primeiro_nome = (nome or "").split(" ")[0]
    st.markdown(f"## Olá, {primeiro_nome}! 👋")
    st.markdown(":gray[Comece uma nova conversa digitando abaixo ou escolha uma sugestão.]")
    st.write("")

    escolhida = None
    colunas = st.columns(2)
    for i, sugestao in enumerate(SUGESTOES):
        if colunas[i % 2].button(sugestao, key=f"sug_{i}", use_container_width=True):
            escolhida = sugestao
    return escolhida
