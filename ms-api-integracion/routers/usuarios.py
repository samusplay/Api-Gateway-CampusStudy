from urllib.parse import quote

from clients.base import forward
from core.config import settings
from core.dependencies import Token
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/usuarios", tags=["Usuarios"])

#Fast Api revisa las Rutas en Orden

@router.get("/buscar")
async def buscar_usuario(email: str, credentials: Token):
    """Busca un usuario activo por correo (para invitar a grupos). 404 si no existe."""
    return await forward("GET", settings.usuarios_url,
                         f"/api/v1/usuarios/buscar?email={quote(email)}",
                         token=credentials.credentials)

@router.get("/me")
async def mi_usuario(credentials: Token):
    """Datos del usuario autenticado (sale del token)."""
    return await forward("GET", settings.usuarios_url, "/api/v1/usuarios/me",
                         token=credentials.credentials)

@router.get("/{usuario_id}")
async def obtener_usuario(usuario_id: int, credentials: Token):
    """Datos básicos de un usuario. 404 si no existe. Requiere token."""
    return await forward("GET", settings.usuarios_url, f"/api/v1/usuarios/{usuario_id}",
                         token=credentials.credentials)
