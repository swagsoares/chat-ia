"""Indicador do status da API (GET /health)."""
import streamlit as st

from core.config import API_URL
from services.api_client import ApiClient, ApiError


@st.cache_data(ttl=15, show_spinner=False)
def _consultar_health() -> dict | None:
    try:
        return ApiClient().health()
    except ApiError:
        return None


def obter_health() -> dict | None:
    return _consultar_health()


def render_status_api() -> None:
    """Linha compacta: API online/offline + modelo em uso."""
    health = obter_health()
    if health is None:
        st.caption(f"🔴 API fora do ar ({API_URL})")
        return
    bolinha = "🟢" if health.get("llm_disponivel") else "🟡"
    st.caption(f"{bolinha} API online · modelo **{health['modelo']}** ({health['provedor']})")
