import asyncio

import httpx
from core.config import settings
from fastapi import HTTPException
from fastapi.responses import JSONResponse, Response

MAX_INTENTOS = 3


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


# --- Reenvía cualquier método y respeta el código de respuesta ---
async def forward(method: str, base_url: str, path: str,
                  body: dict | None = None, token: str | None = None) -> Response:
    """Reenvía la petición al microservicio y devuelve su mismo código y cuerpo."""
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # connect: tiempo para conectarse (si no conecta, el servicio está caído)
    # request_timeout: tiempo para recibir la respuesta (el servicio está vivo, procesando)
    timeout = httpx.Timeout(settings.request_timeout, connect=settings.connect_timeout)

    for intento in range(MAX_INTENTOS):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                r = await client.request(method, f"{base_url}{path}",
                                         json=body, headers=headers)
            return _a_respuesta(r)
        except (httpx.ConnectError, httpx.ConnectTimeout):
            # No llegó al servicio: es seguro reintentar
            if intento < MAX_INTENTOS - 1:
                await asyncio.sleep(0.5 * (2 ** intento))  # 0.5 s, 1 s
        except httpx.TimeoutException:
            # Llegó pero no respondió a tiempo: pudo haberse procesado
            # (ej. un registro), así que NO se reintenta
            break

    raise HTTPException(status_code=503,
                        detail="Servicio no disponible temporalmente")


def _a_respuesta(r: httpx.Response) -> Response:
    """Convierte la respuesta del microservicio en la respuesta del gateway."""
    # 204 / 304 o sin cuerpo: se responde SIN cuerpo (un 204 no puede llevar ni "null")
    if r.status_code in (204, 304) or not r.content:
        return Response(status_code=r.status_code)

    try:
        return JSONResponse(status_code=r.status_code, content=r.json())
    except ValueError:
        # El servicio respondió algo que no es JSON (HTML, texto): no reventamos con 500
        return JSONResponse(status_code=r.status_code,
                            content={"error": r.text[:300] or "Respuesta inválida del servicio"})