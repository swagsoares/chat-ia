"""Cartão do usuário logado + botão Sair, na barra lateral."""
import streamlit as st

from core import state


def _sair() -> None:
    state.deslogar()


def render_usuario_sidebar() -> None:
    usuario = state.usuario() or {}
    col_nome, col_sair = st.columns([0.68, 0.32], vertical_alignment="center")
    col_nome.markdown(f"**{usuario.get('nome', '')}**  \n:gray[@{usuario.get('username', '')}]")
    col_sair.button("Sair", on_click=_sair, use_container_width=True, key="btn_sair")
