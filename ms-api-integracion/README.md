# API Gateway — CampusStudy

Punto **único de entrada** del sistema CampusStudy. El frontend (Next.js) solo habla con el gateway; el gateway reenvía cada petición al microservicio que corresponde y devuelve su respuesta **tal cual** (mismo código y mismo body).

- **Puerto:** `8000`
- **Framework:** FastAPI
- **Docs interactivas:** `http://localhost:8000/docs`
- **Health check:** `GET http://localhost:8000/health`

---

## Tabla de contenido

1. [Arquitectura](#1-arquitectura)
2. [Stack](#2-stack)
3. [Estructura de carpetas](#3-estructura-de-carpetas)
4. [Configuración](#4-configuración)
5. [Cómo correrlo](#5-cómo-correrlo)
6. [Rutas expuestas](#6-rutas-expuestas)
7. [Cómo funciona `forward`](#7-cómo-funciona-forward)
8. [Autenticación y token](#8-autenticación-y-token)
9. [Cómo agregar rutas nuevas](#9-cómo-agregar-rutas-nuevas)
10. [Probar con Postman](#10-probar-con-postman)
11. [Flujo de Git](#11-flujo-de-git)
12. [Problemas comunes](#12-problemas-comunes)

---

## 1. Arquitectura

```
                         ┌──────────────────────────┐
Frontend (Next.js :3000) │      API Gateway :8000   │
        │                │                          │
        └── HTTP ──────► │  routers/auth.py      ───┼──► users-auth        :8081  (Spring Boot + Postgres)
          Bearer token   │  routers/materias.py  ───┼──► materias-service  :8006  (.NET 8 + SQL Server)
                         │  routers/tareas.py    ───┼──► tareas-service    :8001
                         └──────────────────────────┘
```

Responsabilidades del gateway:

| Sí hace | No hace |
|---|---|
| Enrutar cada petición al servicio correcto | Lógica de negocio |
| Exigir que las rutas protegidas traigan `Authorization: Bearer ...` | Validar la firma del JWT (lo hace cada microservicio con el mismo secreto) |
| Reenviar el token al microservicio | Guardar datos |
| Respetar el código de respuesta del servicio (201, 400, 409...) | Transformar las respuestas |
| Reintentar si el servicio no conecta y responder **503** si está caído | |
| CORS para el frontend | |

---

## 2. Stack

| Paquete | Para qué |
|---|---|
| `fastapi` | Framework web |
| `uvicorn` | Servidor ASGI (con `--reload` en desarrollo) |
| `httpx` | Cliente HTTP asíncrono para llamar a los microservicios |
| `pydantic-settings` | Configuración desde variables de entorno / `.env` |
| `PyJWT` | Utilidades JWT |
| `pytest`, `pytest-asyncio` | Tests |

Las versiones exactas están en `requirements.txt`.

---

## 3. Estructura de carpetas

```
ms-api-integracion/
├── clients/
│   └── base.py          # forward() y get_json(): llamadas HTTP a los microservicios
├── core/
│   ├── config.py        # Settings: URLs de servicios, timeouts, secreto JWT
│   └── security.py      # Utilidades de seguridad
├── routers/
│   ├── auth.py          # /api/v1/auth      → users-auth   (público)
│   ├── materias.py      # /api/v1/materias  → materias-service (requiere token)
│   └── tareas.py        # /api/v1/tareas    → tareas-service
├── schemas/
├── services/
├── tests/
├── main.py              # App FastAPI, CORS, registro de routers, /health
├── Dockerfile.dev
├── requirements.txt
├── .env.example         # Plantilla de variables (sí se sube)
└── .env                 # Variables locales (NO se sube)
```

---

## 4. Configuración

`core/config.py` usa **pydantic-settings**. Cada campo se llena en este orden de prioridad:

```
1. Variable de entorno   (la pone docker-compose)   ← gana
2. Archivo .env          (para correr local)
3. Valor por defecto     (en config.py)
```

El nombre se convierte solo: `materias_url` ⇄ `MATERIAS_URL`.

| Variable | Por defecto (local) | En Docker | Descripción |
|---|---|---|---|
| `USUARIOS_URL` | `http://localhost:8005` | `http://users-auth:8081` | users-auth |
| `MATERIAS_URL` | `http://localhost:8006` | `http://materias-service:8006` | materias-service |
| `TAREAS_URL` | `http://localhost:8001` | — | tareas-service |
| `GRUPOS_URL` | `http://localhost:8002` | — | grupos-service |
| `ESTADISTICAS_URL` | `http://localhost:8003` | — | estadisticas-service |
| `NOTIFICACIONES_URL` | `http://localhost:8004` | — | notificaciones-service |
| `JWT_SECRET` | `cambiar-en-produccion` | `${JWT_SECRET}` del `.env` de infra | Secreto compartido con auth |
| `CONNECT_TIMEOUT` | `3.0` | — | Segundos para **conectarse** a un servicio |
| `REQUEST_TIMEOUT` | `10.0` | — | Segundos para recibir la **respuesta** |

> ⚠️ **Dentro de Docker, `localhost` es el propio contenedor del gateway.** Entre contenedores se usa el **nombre del servicio** del compose (`http://materias-service:8006`), nunca `localhost`.

---

## 5. Cómo correrlo

### Opción A — Docker (recomendado, todo el sistema)

Desde el repo `infra-campusstudy`:

```bash
docker compose up -d
docker compose logs -f api-gateway
```

El gateway corre con `uvicorn --reload` y `WATCHFILES_FORCE_POLLING=true`: al guardar un `.py` se recarga solo.

| Acción | Comando |
|---|---|
| Ver logs | `docker compose logs -f api-gateway` |
| Reiniciar (mismo contenedor) | `docker compose restart api-gateway` |
| **Cambiaste `environment`, `ports`, `depends_on` en el compose** | `docker compose up -d` (recrea solo lo que cambió) |
| Forzar contenedor nuevo | `docker compose up -d --force-recreate api-gateway` |
| **Cambiaste `requirements.txt` o el `Dockerfile.dev`** | `docker compose up -d --build api-gateway` |
| Ver qué URL está usando | `docker compose exec api-gateway python -c "from core.config import settings; print(settings.materias_url)"` |
| Ver una variable de entorno | `docker compose exec api-gateway printenv MATERIAS_URL` |

> **`restart` NO toma cambios del compose.** Las variables de entorno se copian al contenedor cuando se **crea**. Si cambias `environment:`, usa `docker compose up -d`.

### Opción B — Local con entorno virtual

```bash
cd ms-api-integracion
python -m venv .venv
source .venv/Scripts/activate      # Git Bash en Windows
# .venv\Scripts\activate           # PowerShell / CMD
# source .venv/bin/activate        # Linux / macOS
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

En VS Code: `Ctrl + Shift + P` → **Python: Select Interpreter** → el de `.venv`. Sin esto, Pylance marca `Import "fastapi" could not be resolved` aunque el código esté bien.

> `.venv/` debe estar en `.gitignore` **y** en `.dockerignore`.

---

## 6. Rutas expuestas

| Método | Ruta | Servicio destino | Token | Estado |
|---|---|---|---|---|
| `GET` | `/health` | — (el propio gateway) | No | ✅ |
| `POST` | `/api/v1/auth/registro` | users-auth | No | ✅ |
| `POST` | `/api/v1/auth/login` | users-auth | No | ✅ |
| `POST` | `/api/v1/materias` | materias-service | **Sí** | ✅ |
| `GET` | `/api/v1/materias` | materias-service | **Sí** | ✅ |
| `GET` | `/api/v1/materias/{materia_id}` | materias-service | **Sí** | ⏳ Pendiente (cuando materias lo implemente) |
| `PUT` | `/api/v1/materias/{materia_id}` | materias-service | **Sí** | ⏳ Pendiente |
| `DELETE` | `/api/v1/materias/{materia_id}` | materias-service | **Sí** | ⏳ Pendiente |
| — | `/api/v1/tareas/...` | tareas-service | — | Ver `routers/tareas.py` |

Los bodies y respuestas de cada ruta son los del **contrato** de cada microservicio: el gateway no los cambia.

---

## 7. Cómo funciona `forward`

`clients/base.py` → `forward()` es el "cartero" del gateway: toma la petición, la reenvía al microservicio y devuelve **el mismo código y el mismo body**.

```python
await forward("POST", settings.materias_url, "/api/v1/materias", body, token=credentials.credentials)
```

| Parámetro | Ejemplo | Para qué |
|---|---|---|
| `method` | `"POST"` | Verbo HTTP |
| `base_url` | `settings.materias_url` | A qué servicio |
| `path` | `"/api/v1/materias"` | Qué endpoint del servicio |
| `body` | `{"nombre": ...}` | JSON a enviar (`None` en GET/DELETE) |
| `token` | `"eyJhbGci..."` | JWT a reenviar como `Authorization: Bearer ...` |

### Timeouts

```python
httpx.Timeout(settings.request_timeout, connect=settings.connect_timeout)   # 10 s / 3 s
```

| Timeout | Qué mide | Si se vence |
|---|---|---|
| `connect` (3 s) | Cuánto esperar para **conectarse** | El servicio está caído → se reintenta |
| `request` (10 s) | Cuánto esperar la **respuesta** ya conectado | El servicio está vivo pero lento → **no** se reintenta |

### Reintentos

| Error | Qué significa | ¿Reintenta? |
|---|---|---|
| `ConnectError` / `ConnectTimeout` | La petición **nunca llegó** | ✅ Sí, hasta 3 intentos (espera 0.5 s y 1 s) |
| `ReadTimeout` u otro `TimeoutException` | La petición **sí llegó**, pero tardó | ❌ No: pudo haberse procesado (ej. un registro); reintentar podría duplicar |

Si todo falla → **503** `Servicio no disponible temporalmente`.

> ⚠️ `httpx.ConnectTimeout` **hereda de `TimeoutException`**, no de `ConnectError`. Por eso el `except` de conexión va **antes** que el de timeout.

> `get_json()` es la versión anterior (solo GET, lanza excepción en errores HTTP). La usan otras partes del gateway: **no borrar**. Para rutas nuevas usar `forward()`.

---

## 8. Autenticación y token

```
1. Front → POST /api/v1/auth/login → users-auth firma un JWT (HS256) con { sub: usuario_id, ... }
2. Front guarda el token
3. Front → GET /api/v1/materias   Authorization: Bearer <token>
4. Gateway: HTTPBearer exige que venga el header (si no → 401/403, no llega al servicio)
5. Gateway → forward(..., token=...) → reenvía el mismo header
6. Materias: valida la firma con el mismo secreto y lee "sub" como usuario_id
```

- El gateway **no descifra** el token: solo verifica que exista y lo pasa. La firma la valida cada microservicio.
- **Todos** los servicios deben usar el **mismo** `JWT_SECRET` (en `infra-campusstudy/.env`). Si no coincide, los servicios responden **401** aunque el token sea recién sacado.
- El `usuario_id` **nunca** se manda en el body: sale del claim `sub` del token.

---

## 9. Cómo agregar rutas nuevas

### Ruta pública (sin token)

```python
from typing import Annotated
from fastapi import APIRouter, Body
from clients.base import forward
from core.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

@router.post("/login")
async def login(body: Annotated[dict, Body()]):
    return await forward("POST", settings.usuarios_url, "/api/v1/auth/login", body)
```

### Ruta protegida (con token)

```python
from typing import Annotated
from fastapi import APIRouter, Body, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from clients.base import forward
from core.config import settings

router = APIRouter(prefix="/api/v1/materias", tags=["Materias"])

bearer = HTTPBearer()
Token = Annotated[HTTPAuthorizationCredentials, Depends(bearer)]   # alias reutilizable


@router.get("/{materia_id}")
async def obtener_materia(materia_id: int, credentials: Token):
    return await forward("GET", settings.materias_url, f"/api/v1/materias/{materia_id}",
                         token=credentials.credentials)


@router.put("/{materia_id}")
async def actualizar_materia(materia_id: int, body: Annotated[dict, Body()], credentials: Token):
    return await forward("PUT", settings.materias_url, f"/api/v1/materias/{materia_id}",
                         body, token=credentials.credentials)
```

### Reglas

- [ ] **Usar `Annotated[...]`**, no `body: dict = Body(...)` ni `= Depends(...)` (Ruff B008).
- [ ] Ruta raíz del router con `""`, no `"/"` → evita el redirect 307 por la barra final.
- [ ] `materia_id: int` en la firma → FastAPI valida el tipo y responde 422 si no es número.
- [ ] Registrar el router **una sola vez** en `main.py`:
  ```python
  for r in (auth, materias, tareas):
      app.include_router(r.router)
  ```
- [ ] Si es un servicio nuevo: agregar `xxx_url` en `core/config.py` y la variable `XXX_URL=http://<servicio>:<puerto>` en el `docker-compose.yml` de infra.
- [ ] Cada archivo de `routers/` tiene **su propio** `prefix`. Copiar un router y olvidar cambiar el prefix hace que las rutas originales desaparezcan (404).

---

## 10. Probar con Postman

### Environment

Crear un environment (ej. `CampusStudy Local`) con:

| Variable | Valor |
|---|---|
| `gateway` | `http://localhost:8000` (sin `/` al final) |
| `token` | *(vacío, lo llena el login)* |

Las URLs se escriben como `{{gateway}}/api/v1/materias`.

### Guardar el token automáticamente

En el request de **login** → pestaña **Scripts** → **Post-response**:

```javascript
if (pm.response.code === 200) {
    pm.environment.set("token", pm.response.json().token);
}
```

### Token heredado

- Colección → **Authorization** → `Bearer Token` → `{{token}}`.
- Carpeta **Auth** → **Authorization** → `No Auth` (login y registro son públicos).
- Los requests dentro de la colección quedan en *Inherit auth from parent*.

### Pruebas mínimas

| Petición | Esperado |
|---|---|
| `GET {{gateway}}/health` | 200 |
| `POST {{gateway}}/api/v1/auth/login` | 200 + token guardado |
| `POST {{gateway}}/api/v1/materias` | 201 |
| Mismo POST con el mismo NRC | 409 |
| `GET {{gateway}}/api/v1/materias` | 200 + arreglo |
| `GET` sin token | 401 / 403 (lo corta el gateway) |
| `GET` con materias apagado (`docker compose stop materias-service`) | 503 |

---

## 11. Flujo de Git

| Rama | Uso |
|---|---|
| `master` | Estable |
| `develop` | Integración |
| `feature/<tarea>` | Una rama por tarea, creada desde `develop` |

```bash
git checkout develop
git pull
git checkout -b feature/rutas-tareas
# ... trabajo ...
git push -u origin feature/rutas-tareas
# Pull Request → develop
```

> Ramas por **tarea**, no por persona. No se suben `.env` ni `.venv/`.

---

## 12. Problemas comunes

| Síntoma | Causa | Solución |
|---|---|---|
| **503 en ~1.5 s** con el servicio arriba | El gateway no conecta: casi siempre la URL apunta a `localhost` dentro de Docker | `printenv MATERIAS_URL` en el contenedor; si falta, `docker compose up -d` para recrearlo |
| Cambié el compose y el gateway sigue igual | `restart` no aplica cambios de `environment` | `docker compose up -d` |
| **503 tras ~10 s** pero el registro sí se creó | El servicio tardó más que `REQUEST_TIMEOUT` (típico en el primer request tras arrancar Spring) | Reintentar; si es constante, revisar logs del servicio |
| **404** `{"detail": "Not Found"}` | La ruta no existe en el gateway: prefix equivocado o router no registrado | Revisar `prefix` del router y `main.py` |
| **401** con un token recién sacado | `JWT_SECRET` distinto entre auth y el servicio | Revisar `infra-campusstudy/.env` |
| **403 / 401** `Not authenticated` | Falta el header `Authorization` | En Postman: Bearer `{{token}}` heredado de la colección |
| Endpoints duplicados en `/docs` / `Duplicate Operation ID` | Router registrado dos veces en `main.py` | Un solo `for r in (...)` |
| `Import "pydantic_settings" could not be resolved` | VS Code usa el Python global | Seleccionar el intérprete del `.venv` |
| Warning `B008 Do not perform function call Body/Depends in argument defaults` | Sintaxis vieja de FastAPI | Usar `Annotated[dict, Body()]` / `Annotated[..., Depends(...)]` |
| `class Config` deprecado | Sintaxis de Pydantic v1 | `model_config = SettingsConfigDict(env_file=".env")` |