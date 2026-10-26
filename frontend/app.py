"""Entrada do front-end e roteamento de páginas (st.navigation).

Rodar:  streamlit run app.py   (porta 8501)

- Sem login: só a página de Login existe.
- Com login: páginas Chat e Status, com o usuário e o status da API na barra lateral.
"""
import streamlit as st

from components.status_api import render_status_api
from components.usuario_sidebar import render_usuario_sidebar
from core import state

st.set_page_config(page_title="Chat IA", page_icon="💬", layout="wide", initial_sidebar_state="expanded")
state.init_state()

pagina_login = st.Page("pages/login.py", title="Entrar", icon=":material/login:")
pagina_chat = st.Page("pages/chat.py", title="Chat", icon=":material/chat:", default=True)
pagina_status = st.Page("pages/status.py", title="Status", icon=":material/monitor_heart:")

if state.esta_logado():
    navegacao = st.navigation([pagina_chat, pagina_status], position="top")
    with st.sidebar:
        render_usuario_sidebar()
        render_status_api()
        st.divider()
else:
    navegacao = st.navigation([pagina_login], position="hidden")

navegacao.run()
