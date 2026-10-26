"""Página de status: saúde da API, modelo em uso e conta do usuário."""
import streamlit as st

from components.status_api import obter_health
from core import state
from core.config import API_URL
from core.erros import chamar_api

st.markdown("## Status do sistema")

health = obter_health()
col1, col2, col3 = st.columns(3)
col1.metric("API", "Online" if health else "Fora do ar")
col2.metric("Provedor do modelo", health["provedor"] if health else "—")
col3.metric("Modelo", health["modelo"] if health else "—")

if health and not health["llm_disponivel"]:
    st.warning("A API está no ar, mas o modelo de linguagem está indisponível. "
               "As mensagens vão responder com erro 503 até ele voltar.", icon="🟡")

st.caption(f"Endereço da API: `{API_URL}` · documentação em [{API_URL}/docs]({API_URL}/docs)")

st.divider()
st.markdown("### Sua conta")
me = chamar_api(state.api().me)
if me:
    st.markdown(f"**Nome:** {me['nome']}  \n**Usuário:** @{me['username']}  \n**Conta criada em:** {me['criado_em']}")

if st.button("Atualizar status"):
    st.cache_data.clear()
    st.rerun()
