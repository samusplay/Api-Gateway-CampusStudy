from typing import Annotated

from clients.base import forward
from core.config import settings
from fastapi import APIRouter, Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/api/v1/notificaciones", tags=["Notificaciones"])

bearer = HTTPBearer()
Token = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
ObjectId = Annotated[str, Path(pattern="^[a-f0-9]{24}$")]


@router.get("/me")
async def mis_notificaciones(credentials: Token):
    return await forward("GET", settings.notificaciones_url, "/api/v1/notificaciones/me",
                         token=credentials.credentials)


@router.patch("/{notificacion_id}/leida")
async def marcar_leida(notificacion_id: ObjectId, credentials: Token):
    return await forward("PATCH", settings.notificaciones_url,
                         f"/api/v1/notificaciones/{notificacion_id}/leida",
                         token=credentials.credentials)