"""Página principal do chat.

O histórico é SEMPRE lido da API (GET /conversas/{id}) a cada execução;
a sessão guarda apenas o id da conversa ativa.
"""
import streamlit as st

from components.boas_vindas import render_boas_vindas
from components.caixa_envio import render_caixa_envio
from components.lista_conversas import render_lista_conversas
from components.mensagens import render_mensagem, render_mensagens
from core import state
from core.erros import chamar_api
from services.api_client import ApiError, NaoEncontradoError, SessaoExpiradaError

api = state.api()

# ---- Barra lateral: lista de conversas ----------------------------------- #
with st.sidebar:
    render_lista_conversas()

# ---- Carrega a conversa ativa da API -------------------------------------- #
conversa_id = state.conversa_ativa()
conversa = None
if conversa_id is not None:
    try:
        conversa = api.abrir_conversa(conversa_id)
    except NaoEncontradoError:
        state.definir_conversa_ativa(None)  # foi excluída: volta para "nova conversa"
        st.rerun()
    except SessaoExpiradaError:
        chamar_api(api.abrir_conversa, conversa_id)  # trata o 401 (volta ao login)
    except ApiError as exc:
        st.error(exc.mensagem, icon="⚠️")
        st.stop()

# ---- Área do chat ---------------------------------------------------------- #
sugestao = None
if conversa and conversa["mensagens"]:
    st.markdown(f"### {conversa['titulo']}")
    render_mensagens(conversa["mensagens"])
else:
    sugestao = render_boas_vindas(state.usuario()["nome"])

texto = render_caixa_envio() or sugestao

if texto:
    # Conversa nova: cria na API só agora, no primeiro envio
    if conversa_id is None:
        nova = chamar_api(api.criar_conversa)
        if nova is None:
            st.stop()
        conversa_id = nova["id"]
        state.definir_conversa_ativa(conversa_id)

    render_mensagem("user", texto)
    with st.chat_message("assistant", avatar=":material/smart_toy:"):
        with st.spinner("Pensando…"):
            resultado = chamar_api(api.enviar_mensagem, conversa_id, texto)
        if resultado is None:
            st.caption("Sua mensagem não foi salva. Tente enviar de novo em instantes.")
        else:
            st.rerun()  # recarrega histórico e título a partir da API
