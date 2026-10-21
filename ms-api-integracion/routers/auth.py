from typing import Annotated

from clients.base import forward
from core.config import settings
from fastapi import APIRouter, Body

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/registro", status_code=201)
async def registro(body: Annotated[dict, Body()]):
    """Crea una cuenta nueva. Público: no requiere token."""
    return await forward("POST", settings.usuarios_url, "/api/v1/auth/registro", body)


@router.post("/login")
async def login(body: Annotated[dict, Body()]):
    """Inicia sesión y devuelve el token. Público: no requiere token."""
    return await forward("POST", settings.usuarios_url, "/api/v1/auth/login", body)

@router.post("/validate")
async def validar_token(body: Annotated[dict, Body()]):
    """Indica si un token es válido y de quién es. Público: el token viaja en el body."""
    return await forward("POST", settings.usuarios_url, "/api/v1/auth/validate", body)