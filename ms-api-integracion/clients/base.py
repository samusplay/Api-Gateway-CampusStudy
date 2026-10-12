import asyncio

import httpx
from core.config import settings
from fastapi import HTTPException
from fastapi.responses import JSONResponse


# --- Original de Julián: lo usan materias y tareas. NO BORRAR ---
async def get_json(base_url: str, path: str, token: str | None = None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    last_error = None
    for intento in range(3):
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                r = await client.get(f"{base_url}{path}", headers=headers)
                r.raise_for_status()
                return r.json()
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last_error = e
            await asyncio.sleep(0.5 * (2 ** intento))
    raise last_error


# --- Nuevo: reenvía cualquier método y respeta el código de respuesta ---
async def forward(method: str, base_url: str, path: str,
                  body: dict | None = None, token: str | None = None) -> JSONResponse:
    """Reenvía la petición al microservicio y devuelve su mismo código y cuerpo."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    for intento in range(3):
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
                r = await client.request(method, f"{base_url}{path}",
                                         json=body, headers=headers)
            content = r.json() if r.content else None
            return JSONResponse(status_code=r.status_code, content=content)
        except httpx.ConnectError:
            # No llegó al servicio: es seguro reintentar
            await asyncio.sleep(0.5 * (2 ** intento))
        except httpx.TimeoutException:
            # Pudo haberse procesado (ej. un registro): no se reintenta
            break

    raise HTTPException(status_code=503,
                        detail="Servicio no disponible temporalmente")