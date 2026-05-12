"""
Entry point da aplicação FastAPI.
Configura middlewares, CORS, rate limiting e registra os routers.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.core.security import SecurityHeadersMiddleware, BodySizeLimitMiddleware
from app.db.base import Base
from app.db.session import engine
from app.api.v1.endpoints import registro, diagnostico

# Importa os models para que o SQLAlchemy os registre antes de criar as tabelas
import app.models.registro  # noqa: F401

settings = get_settings()

# Configura o rate limiter usando o IP remoto como chave
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Na inicialização: cria as tabelas do banco de dados.
    No encerramento: pode liberar recursos (ex: fechar conexões).
    """
    # Cria as tabelas no banco de dados (se não existirem)
    Base.metadata.create_all(bind=engine)
    yield
    # Aqui podemos adicionar limpeza de recursos no futuro


# ---------------------------------------------------------------------------
# Instância da aplicação FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Focus Log API",
    description=(
        "API REST para registro de sessões de trabalho/estudo com nível de foco "
        "e geração de diagnóstico inteligente de produtividade."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    # Em produção, oculta detalhes de erros internos
    debug=settings.debug,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middlewares (ordem importa — os últimos na lista são executados primeiro)
# ---------------------------------------------------------------------------

# 1. Rate limiting (SlowAPI)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# 2. Limite de tamanho do corpo (10KB)
app.add_middleware(BodySizeLimitMiddleware)

# 3. Headers de segurança OWASP
app.add_middleware(SecurityHeadersMiddleware)

# 4. CORS configurável via env var (nunca '*' em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Handler global de erros não tratados
# Garante que nenhum stack trace vaze para o cliente (OWASP API8)
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Captura exceções não tratadas e retorna uma resposta genérica.
    Evita vazar stack traces em produção.
    """
    if settings.debug:
        # Em modo debug, expõe o erro para facilitar o desenvolvimento
        raise exc

    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor. Por favor, tente novamente mais tarde."},
    )


# ---------------------------------------------------------------------------
# Registro dos routers
# ---------------------------------------------------------------------------
app.include_router(
    registro.router,
    prefix="/api/v1",
    tags=["Registros de Foco"],
)

app.include_router(
    diagnostico.router,
    prefix="/api/v1",
    tags=["Diagnóstico de Produtividade"],
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Saúde da API"], summary="Health check")
async def health_check() -> dict:
    """Verifica se a API está funcionando corretamente."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "debug": settings.debug,
    }


@app.get("/", include_in_schema=False)
async def root_redirect() -> RedirectResponse:
    """Redireciona a raiz para a documentação interativa (Swagger UI)."""
    return RedirectResponse(url="/docs")
