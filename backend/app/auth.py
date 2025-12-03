# auth.py — Middleware de autenticação simples por API Key

import os
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

# Configuração da API Key
# Em produção, usar variável de ambiente
API_KEY = os.getenv("PORTAL_API_KEY", "dev-api-key-change-in-production")
API_KEY_NAME = "X-API-Key"

# Headers e Query params para API Key
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    api_key_header: Optional[str] = Security(api_key_header),
    api_key_query: Optional[str] = Security(api_key_query),
) -> str:
    """
    Valida a API Key fornecida via header ou query parameter.
    
    Uso em rotas:
        @router.get("/protected", dependencies=[Depends(get_api_key)])
        async def protected_route():
            ...
    """
    if api_key_header == API_KEY:
        return api_key_header
    if api_key_query == API_KEY:
        return api_key_query
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="API Key inválida ou não fornecida",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def require_api_key():
    """
    Dependency para exigir API Key em rotas.
    
    Uso:
        router = APIRouter(dependencies=[Depends(require_api_key())])
    """
    return Security(get_api_key)


# Rotas públicas que não exigem autenticação
PUBLIC_ROUTES = [
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
]


def is_public_route(path: str) -> bool:
    """Verifica se a rota é pública."""
    return any(path.startswith(route) for route in PUBLIC_ROUTES)
