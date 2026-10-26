from pydantic import BaseModel


class ErroSaida(BaseModel):
    """Formato padrão de erro devolvido pela API (o front exibe o campo detail)."""

    detail: str


class HealthSaida(BaseModel):
    status: str
    provedor: str
    modelo: str
    llm_disponivel: bool
    versao: str


# Respostas de erro reutilizadas na documentação (/docs) das rotas
RESPOSTA_401 = {401: {"model": ErroSaida, "description": "Token ausente, inválido ou expirado"}}
RESPOSTA_404 = {404: {"model": ErroSaida, "description": "Conversa inexistente (ou de outro usuário)"}}
RESPOSTA_503 = {503: {"model": ErroSaida, "description": "Modelo de linguagem indisponível"}}
