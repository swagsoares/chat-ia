from app.llm.provider import LLMProvider
from app.schemas.comum import HealthSaida

VERSAO_API = "1.0.0"


class HealthService:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def status(self) -> HealthSaida:
        return HealthSaida(
            status="ok",
            provedor=self.llm.nome_provedor,
            modelo=self.llm.nome_modelo,
            llm_disponivel=self.llm.disponivel(),
            versao=VERSAO_API,
        )
