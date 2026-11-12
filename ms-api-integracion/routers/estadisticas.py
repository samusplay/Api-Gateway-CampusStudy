from typing import Annotated
from urllib.parse import urlencode

from clients.base import forward
from core.config import settings
from fastapi import APIRouter, Depends, Path, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(prefix="/api/v1/estadisticas", tags=["Estadísticas"])

bearer = HTTPBearer()
Token = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
Periodo = Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}$")]


@router.get("/me")
async def mis_estadisticas(
    credentials: Token,
    periodo: Periodo = None,
    materia_id: Annotated[int | None, Query(gt=0)] = None,
):
    filtros = {k: v for k, v in {"periodo": periodo, "materia_id": materia_id}.items() if v is not None}
    path = "/api/v1/estadisticas/me" + (f"?{urlencode(filtros)}" if filtros else "")
    return await forward("GET", settings.estadisticas_url, path, token=credentials.credentials)


@router.get("/materia/{materia_id}")
async def estadisticas_materia(
    materia_id: Annotated[int, Path(gt=0)],
    credentials: Token,
    periodo: Periodo = None,
):
    path = f"/api/v1/estadisticas/materia/{materia_id}" + (f"?{urlencode({'periodo': periodo})}" if periodo else "")
    return await forward("GET", settings.estadisticas_url, path, token=credentials.credentials)


@router.get("/grupo/{grupo_id}")
async def estadisticas_grupo(grupo_id: Annotated[int, Path(gt=0)], credentials: Token):
    return await forward("GET", settings.estadisticas_url, f"/api/v1/estadisticas/grupo/{grupo_id}",
                         token=credentials.credentials)