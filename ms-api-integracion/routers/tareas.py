from typing import Annotated

from clients.base import forward
from core.config import settings
from core.dependencies import Token
from fastapi import APIRouter, Body

router = APIRouter(prefix="/api/v1/tareas", tags=["Tareas"])


@router.post("", status_code=201)
async def crear_tarea(body: Annotated[dict, Body()], credentials: Token):
    """Crea una tarea del estudiante autenticado. Requiere token."""
    return await forward("POST", settings.tareas_url, "/api/v1/tareas",
                         body, token=credentials.credentials)