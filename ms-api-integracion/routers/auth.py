from clients.base import forward
from core.config import settings
from fastapi import APIRouter, Body

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/registro", status_code=201)
async def registro(body: dict = Body(...)):
    """Crea una cuenta nueva. Público: no requiere token."""
    return await forward("POST", settings.usuarios_url, "/api/v1/auth/registro", body)

@router.post("/login")
async def login(body: dict = Body(...)):
    """Inicia sesión y devuelve el token. Público: no requiere token."""
    return await forward("POST", settings.usuarios_url, "/api/v1/auth/login", body)