"""Página de login e cadastro."""
import streamlit as st

from components.status_api import render_status_api
from core import state
from services.api_client import ApiClient, ApiError

_, centro, _ = st.columns([1, 2, 1])

with centro:
    st.markdown("# 💬 Chat IA")
    st.markdown(":gray[Entre para ver suas conversas ou crie uma conta.]")
    render_status_api()

    aviso = st.session_state.pop("aviso_login", None)
    if aviso:
        st.warning(aviso, icon="🔒")

    aba_entrar, aba_criar = st.tabs(["Entrar", "Criar conta"])

    with aba_entrar:
        with st.form("form_login", border=False):
            username = st.text_input("Usuário", placeholder="seu.usuario")
            senha = st.text_input("Senha", type="password")
            enviar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if enviar:
            if not username or not senha:
                st.warning("Preencha usuário e senha.")
            else:
                try:
                    resposta = ApiClient().login(username.strip(), senha)
                    state.logar(resposta["access_token"], resposta["usuario"])
                    st.rerun()
                except ApiError as exc:
                    st.error(exc.mensagem, icon="⚠️")

    with aba_criar:
        with st.form("form_registro", border=False):
            nome = st.text_input("Nome", placeholder="Como quer ser chamado")
            novo_username = st.text_input("Usuário", placeholder="letras, números, _ . -", key="reg_user")
            nova_senha = st.text_input("Senha", type="password", help="Mínimo de 6 caracteres", key="reg_senha")
            confirmar = st.text_input("Confirmar senha", type="password", key="reg_conf")
            criar = st.form_submit_button("Criar conta", type="primary", use_container_width=True)

        if criar:
            if nova_senha != confirmar:
                st.warning("As senhas não conferem.")
            else:
                try:
                    cliente = ApiClient()
                    cliente.registrar(novo_username.strip(), nome.strip(), nova_senha)
                    resposta = cliente.login(novo_username.strip(), nova_senha)  # já entra direto
                    state.logar(resposta["access_token"], resposta["usuario"])
                    st.rerun()
                except ApiError as exc:
                    st.error(exc.mensagem, icon="⚠️")
