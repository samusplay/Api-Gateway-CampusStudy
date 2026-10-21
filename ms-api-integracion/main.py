from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, grupos, materias, tareas, usuarios

app = FastAPI(
    title="CampusStudy - API Gateway",
    description="Punto único de entrada e integración de microservicios",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers (una sola vez cada uno)
# auth: rutas públicas | materias y tareas: requieren token
for r in (auth, materias,grupos, tareas,usuarios):
    app.include_router(r.router)


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "servicio": "api-gateway"}