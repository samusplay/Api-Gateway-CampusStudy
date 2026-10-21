from typing import Annotated

from clients.base import forward
from core.config import settings
from core.dependencies import Token
from fastapi import APIRouter, Body

router = APIRouter(prefix="/api/v1/materias", tags=["Materias"])


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


@router.get("/{materia_id}")
async def obtener_materia(materia_id: int, credentials: Token):
    """Detalle de una materia del estudiante. 404 si no existe o no es suya."""
    return await forward("GET", settings.materias_url, f"/api/v1/materias/{materia_id}",
                         token=credentials.credentials)


@router.put("/{materia_id}")
async def actualizar_materia(materia_id: int, body: Annotated[dict, Body()], credentials: Token):
    """Reemplaza nombre, NRC y descripción. 409 si el NRC ya lo usa otra materia suya."""
    return await forward("PUT", settings.materias_url, f"/api/v1/materias/{materia_id}",
                         body, token=credentials.credentials)


@router.delete("/{materia_id}", status_code=204)
async def eliminar_materia(materia_id: int, credentials: Token):
    """Elimina una materia del estudiante. 204 sin cuerpo; 404 si no existe o no es suya."""
    return await forward("DELETE", settings.materias_url, f"/api/v1/materias/{materia_id}",
                         token=credentials.credentials)