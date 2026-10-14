from typing import Annotated

from clients.base import forward
from core.config import settings
from fastapi import APIRouter, Body, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/api/v1/materias", tags=["Materias"])

# Lee el header "Authorization: Bearer <token>" de la petición del front
bearer = HTTPBearer()

# Alias reutilizable: "el token del usuario, sacado del header"
Token = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]


@router.post("", status_code=201)
async def crear_materia(body: Annotated[dict, Body()], credentials: Token):
    """Crea una materia del estudiante autenticado. Requiere token."""
    return await forward("POST", settings.materias_url, "/api/v1/materias",
                         body, token=credentials.credentials)


@router.get("")
async def listar_materias(credentials: Token):
    """Lista las materias del estudiante autenticado. Requiere token."""
    return await forward("GET", settings.materias_url, "/api/v1/materias",
                         token=credentials.credentials)