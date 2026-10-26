"""Barra lateral com o botão "Nova conversa" e a lista de conversas do usuário."""
import streamlit as st

from core import state
from core.erros import chamar_api


def _abrir(conversa_id: int) -> None:
    state.definir_conversa_ativa(conversa_id)


def _nova_conversa() -> None:
    # Conversa vazia: só é criada na API quando a 1ª mensagem for enviada
    state.definir_conversa_ativa(None)


def render_lista_conversas() -> None:
    st.button(
        "➕  Nova conversa", type="primary", use_container_width=True,
        on_click=_nova_conversa, key="btn_nova_conversa",
    )

    conversas = chamar_api(state.api().listar_conversas)
    if conversas is None:
        return

    st.markdown("##### Suas conversas")
    if not conversas:
        st.caption("Nenhuma conversa ainda. Envie uma mensagem para começar.")
        return

    ativa = state.conversa_ativa()
    for conversa in conversas:
        col_titulo, col_excluir = st.columns([0.84, 0.16], gap="small", vertical_alignment="center")
        col_titulo.button(
            conversa["titulo"],
            key=f"conv_{conversa['id']}",
            type="secondary" if conversa["id"] != ativa else "tertiary",
            icon="💬" if conversa["id"] == ativa else None,
            use_container_width=True,
            on_click=_abrir, args=(conversa["id"],),
            help=f"{conversa['total_mensagens']} mensagens",
        )
        with col_excluir.popover("", icon=":material/delete:", use_container_width=True):
            st.markdown(f"Excluir **{conversa['titulo']}**?")
            if st.button("Excluir", key=f"del_{conversa['id']}", type="primary"):
                if chamar_api(state.api().excluir_conversa, conversa["id"]):
                    if ativa == conversa["id"]:
                        state.definir_conversa_ativa(None)
                    st.rerun()
