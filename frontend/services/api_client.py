"""ÚNICO módulo do front que faz chamadas HTTP.

Fluxo: pages -> components -> services/api_client.py -> API (FastAPI).

- Todas as requisições usam `requests` com timeout.
- Qualquer falha vira ApiError com uma mensagem amigável em português;
  a tela nunca recebe um traceback.
- 401 vira SessaoExpiradaError, para o front mandar o usuário ao login.
"""
from typing import Any

import requests

from core.config import API_TIMEOUT, API_URL


class ApiError(Exception):
    """Erro já traduzido para o usuário final."""

    def __init__(self, mensagem: str, status: int | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


class SessaoExpiradaError(ApiError):
    """401: token ausente, inválido ou expirado."""


class NaoEncontradoError(ApiError):
    """404: recurso não existe (ou não pertence ao usuário)."""


class ModeloIndisponivelError(ApiError):
    """503: o modelo de linguagem está fora do ar."""


MENSAGENS_PADRAO = {
    400: "Requisição inválida.",
    401: "Sua sessão expirou. Faça login novamente.",
    404: "Não encontramos o que você pediu.",
    409: "Esse registro já existe.",
    422: "Alguns dados enviados são inválidos.",
    503: "O modelo de linguagem está indisponível no momento. Tente novamente em instantes.",
}


class ApiClient:
    def __init__(self, base_url: str = API_URL, token: str | None = None, timeout: float = API_TIMEOUT):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout

    # ------------------------------------------------------------------ #
    # Núcleo: uma única função faz todas as requisições
    # ------------------------------------------------------------------ #
    def _request(self, metodo: str, caminho: str, json: Any = None, autenticado: bool = True) -> Any:
        headers = {"Accept": "application/json"}
        if autenticado:
            if not self.token:
                raise SessaoExpiradaError("Você precisa fazer login.", 401)
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            resp = requests.request(
                metodo, f"{self.base_url}{caminho}", json=json, headers=headers, timeout=self.timeout
            )
        except requests.exceptions.Timeout:
            raise ApiError("A API demorou demais para responder. Tente novamente.") from None
        except requests.exceptions.ConnectionError:
            raise ApiError(
                f"Não foi possível conectar à API em {self.base_url}. Verifique se o back-end está rodando."
            ) from None
        except requests.exceptions.RequestException:
            raise ApiError("Falha inesperada de comunicação com a API.") from None

        if resp.status_code == 204:
            return None
        if resp.ok:
            try:
                return resp.json()
            except ValueError:
                raise ApiError("A API devolveu uma resposta em formato inesperado.", resp.status_code) from None

        self._levantar_erro(resp)

    @staticmethod
    def _levantar_erro(resp: requests.Response) -> None:
        detalhe = None
        try:
            corpo = resp.json()
            if isinstance(corpo.get("detail"), str):
                detalhe = corpo["detail"]
        except (ValueError, AttributeError):
            pass

        status = resp.status_code
        mensagem = detalhe or MENSAGENS_PADRAO.get(status) or f"Erro na API (código {status})."
        if status >= 500 and status != 503:
            mensagem = "A API encontrou um erro interno. Tente novamente mais tarde."

        if status == 401:
            raise SessaoExpiradaError(mensagem, status)
        if status == 404:
            raise NaoEncontradoError(mensagem, status)
        if status == 503:
            raise ModeloIndisponivelError(mensagem, status)
        raise ApiError(mensagem, status)

    # ------------------------------------------------------------------ #
    # Endpoints
    # ------------------------------------------------------------------ #
    def health(self) -> dict:
        return self._request("GET", "/health", autenticado=False)

    def registrar(self, username: str, nome: str, senha: str) -> dict:
        return self._request(
            "POST", "/auth/registro", json={"username": username, "nome": nome, "senha": senha}, autenticado=False
        )

    def login(self, username: str, senha: str) -> dict:
        return self._request("POST", "/auth/login", json={"username": username, "senha": senha}, autenticado=False)

    def me(self) -> dict:
        return self._request("GET", "/auth/me")

    def listar_conversas(self) -> list[dict]:
        return self._request("GET", "/conversas")

    def criar_conversa(self, titulo: str | None = None) -> dict:
        return self._request("POST", "/conversas", json={"titulo": titulo})

    def abrir_conversa(self, conversa_id: int) -> dict:
        return self._request("GET", f"/conversas/{conversa_id}")

    def excluir_conversa(self, conversa_id: int) -> bool:
        self._request("DELETE", f"/conversas/{conversa_id}")  # 204 sem corpo
        return True

    def enviar_mensagem(self, conversa_id: int, conteudo: str) -> dict:
        return self._request("POST", f"/conversas/{conversa_id}/mensagens", json={"conteudo": conteudo})
