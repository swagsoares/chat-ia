"""Executa chamadas à API e mostra erros de forma amigável (sem traceback)."""
from typing import Any, Callable

import streamlit as st

from core import state
from services.api_client import ApiError, SessaoExpiradaError


def chamar_api(funcao: Callable[..., Any], *args, mostrar_erro: bool = True, **kwargs) -> Any | None:
    """Chama uma função do ApiClient.

    - Sucesso: devolve o resultado.
    - 401: limpa a sessão e volta para o login.
    - Outros erros: mostra st.error com a mensagem amigável e devolve None.
    """
    try:
        return funcao(*args, **kwargs)
    except SessaoExpiradaError as exc:
        state.deslogar()
        st.session_state["aviso_login"] = exc.mensagem
        st.rerun()
    except ApiError as exc:
        if mostrar_erro:
            st.error(exc.mensagem, icon="⚠️")
        return None
