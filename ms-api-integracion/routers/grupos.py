from typing import Annotated

from clients.base import forward
from core.config import settings
from core.dependencies import Token
from fastapi import APIRouter, Body

router = APIRouter(prefix="/api/v1/grupos", tags=["Grupos"])


@router.post("", status_code=201)
async def crear_grupo(body: Annotated[dict, Body()], credentials: Token):
    """Crea un grupo en una materia del estudiante. El creador queda como líder."""
    return await forward("POST", settings.grupos_url, "/api/v1/grupos",
                         body, token=credentials.credentials)


@router.get("")
async def listar_grupos(credentials: Token):
    """Lista los grupos donde el estudiante es integrante."""
    return await forward("GET", settings.grupos_url, "/api/v1/grupos",
                         token=credentials.credentials)


@router.get("/{grupo_id}")
async def obtener_grupo(grupo_id: int, credentials: Token):
    """Consulta un grupo. 404 si no existe o el estudiante no pertenece a él."""
    return await forward("GET", settings.grupos_url, f"/api/v1/grupos/{grupo_id}",
                         token=credentials.credentials)