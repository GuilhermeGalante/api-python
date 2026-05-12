"""
Módulo de segurança: headers HTTP, autenticação por API Key e validações OWASP.
"""
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import get_settings, Settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que adiciona headers de segurança em todas as respostas.
    Mitiga: API8 — Security Misconfiguration (OWASP API Security Top 10).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # Impede que o browser detecte automaticamente o tipo de conteúdo
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Impede que a aplicação seja carregada em iframes (proteção contra clickjacking)
        response.headers["X-Frame-Options"] = "DENY"

        # Força HTTPS em produção por 1 ano
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

        # Desativa cache para respostas da API (evita vazamento de dados sensíveis)
        response.headers["Cache-Control"] = "no-store"

        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware que limita o tamanho do corpo da requisição a 10KB.
    Mitiga: API4 — Unrestricted Resource Consumption (OWASP API Security Top 10).
    """

    MAX_BODY_SIZE = 10 * 1024  # 10 KB

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > self.MAX_BODY_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Corpo da requisição excede o limite de 10KB.",
            )

        return await call_next(request)


async def verify_api_key(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """
    Dependência FastAPI que valida a API Key no header X-API-Key.
    Se a API Key não estiver configurada (modo dev), a autenticação é ignorada.
    Mitiga: API2 — Broken Authentication (OWASP API Security Top 10).
    """
    if not settings.auth_enabled:
        # Modo desenvolvimento: sem autenticação
        return

    api_key = request.headers.get("X-API-Key")

    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida ou ausente. Forneça o header X-API-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
