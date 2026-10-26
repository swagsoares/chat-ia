from fastapi import APIRouter, Depends

from app.llm.provider import LLMProvider, get_llm_provider
from app.schemas.comum import HealthSaida
from app.services.health_service import HealthService

router = APIRouter(tags=["Saúde"])


@router.get(
    "/health",
    response_model=HealthSaida,
    summary="Verifica se a API está no ar",
    description="Rota pública. Informa se a API está respondendo, qual provedor/modelo de "
                "linguagem está configurado no .env e se ele está disponível.",
)
def health(llm: LLMProvider = Depends(get_llm_provider)) -> HealthSaida:
    return HealthService(llm).status()
