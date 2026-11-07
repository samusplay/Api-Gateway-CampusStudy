from typing import Annotated

from clients.base import forward
from core.config import settings
from core.dependencies import Token
from fastapi import APIRouter, Body, Request

router = APIRouter(prefix="/api/v1/tareas", tags=["Tareas"])


@router.post("", status_code=201)
async def crear_tarea(body: Annotated[dict, Body()], credentials: Token):
    """Crea una tarea del estudiante autenticado. Requiere token."""
    return await forward("POST", settings.tareas_url, "/api/v1/tareas",
                         body, token=credentials.credentials)


@router.get("")
async def listar_tareas(request: Request, credentials: Token):
    """Lista las tareas del estudiante. Opcional: ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD"""
    query = f"?{request.url.query}" if request.url.query else ""
    return await forward("GET", settings.tareas_url, f"/api/v1/tareas{query}",
                         token=credentials.credentials)

@router.put("/{tarea_id}/estado")
async def cambiar_estado(tarea_id: int, body: Annotated[dict, Body()], credentials: Token):
    """Cambia el estado: pendiente → en_progreso → completada (o cancelada)."""
    return await forward("PUT", settings.tareas_url, f"/api/v1/tareas/{tarea_id}/estado",
                         body, token=credentials.credentials)

@router.delete("/{tarea_id}", status_code=204)
async def cancelar_tarea(tarea_id: int, credentials: Token):
    """Cancela la tarea (eliminación lógica). 204 sin cuerpo."""
    return await forward("DELETE", settings.tareas_url, f"/api/v1/tareas/{tarea_id}",
                         token=credentials.credentials)