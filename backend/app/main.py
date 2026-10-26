"""Ponto de entrada da API: cria o FastAPI, registra os routers e os
tratadores de erro. Para rodar:  uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db
from app.core.exceptions import ErroDominio
from app.routers import auth, conversas, health
from app.services.health_service import VERSAO_API


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()  # cria as tabelas no SQLite se ainda não existirem
    yield


DESCRICAO = """
API do **Chat de IA Generativa com múltiplas conversas** (Checkpoint de Front-end — FIAP).

**Como testar por aqui:**
1. `POST /auth/registro` para criar um usuário;
2. `POST /auth/login` e copie o `access_token`;
3. clique em **Authorize** (cadeado) e cole o token;
4. use as rotas de **Conversas**.

Camadas: *routers* (HTTP) → *services* (regras) → *repositories* (SQLite) e *llm/provider* (modelo).
"""

app = FastAPI(
    title=settings.app_nome,
    description=DESCRICAO,
    version=VERSAO_API,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Saúde", "description": "Status da API e do modelo de linguagem."},
        {"name": "Autenticação", "description": "Cadastro, login (JWT) e usuário logado."},
        {"name": "Conversas", "description": "Criar, listar, abrir e excluir conversas e trocar mensagens. "
                                             "Exigem `Authorization: Bearer <token>`."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ErroDominio)
async def tratar_erro_dominio(_: Request, exc: ErroDominio) -> JSONResponse:
    """Converte exceções da camada de serviço no código HTTP correto."""
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.mensagem}, headers=headers)


@app.exception_handler(RequestValidationError)
async def tratar_validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Mantém o 422 do Pydantic, mas acrescenta uma mensagem legível para o front."""
    erros = exc.errors()
    primeiro = erros[0] if erros else {}
    campo = ".".join(str(p) for p in primeiro.get("loc", [])[1:]) or "requisição"
    mensagem = primeiro.get("msg", "dados inválidos").replace("Value error, ", "")
    return JSONResponse(
        status_code=422,
        content={"detail": f"Campo inválido ({campo}): {mensagem}", "erros": jsonable(erros)},
    )


def jsonable(erros: list) -> list:
    # Remove objetos não serializáveis (ex.: exceções dentro de 'ctx')
    return [{k: v for k, v in e.items() if k in ("loc", "msg", "type")} for e in erros]


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(conversas.router)
