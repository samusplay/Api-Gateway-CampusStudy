from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    tareas_url: str = "http://localhost:8001"
    grupos_url: str = "http://localhost:8082"
    estadisticas_url: str = "http://localhost:8003"
    notificaciones_url: str = "http://localhost:8004"
    usuarios_url: str = "http://localhost:8005"
    materias_url: str = "http://localhost:8006"
    jwt_secret: str = "cambiar-en-produccion"
    connect_timeout: float = 3.0   # conectar: si no conecta, está caído
    request_timeout: float = 10.0  # respuesta: el servicio está vivo pero procesando


settings = Settings()