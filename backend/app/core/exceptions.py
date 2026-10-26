"""Exceções de domínio.

A camada de serviço lança estas exceções; o main.py as converte em respostas
HTTP com o código certo. Assim as rotas não precisam de if/else de regra de
negócio, e o serviço não conhece nada de HTTP.
"""


class ErroDominio(Exception):
    status_code: int = 400

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class CredenciaisInvalidasError(ErroDominio):
    status_code = 401


class NaoAutenticadoError(ErroDominio):
    status_code = 401


class UsuarioJaExisteError(ErroDominio):
    status_code = 409


class ConversaNaoEncontradaError(ErroDominio):
    status_code = 404


class LLMIndisponivelError(ErroDominio):
    status_code = 503
