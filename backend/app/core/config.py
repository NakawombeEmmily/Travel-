from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str
    ENCRYPTION_KEY: str
    DATABASE_URL: str
    DATABASE_URL_DIRECT: str
    ADMIN_DATABASE_URL: str
    REDIS_URL: str
    CORS_ORIGINS: str = "http://localhost:5173"
    FRONTEND_URL: str = "http://localhost:5173"
    STORAGE_ENDPOINT: str = "localhost:9000"
    STORAGE_BUCKET: str = "travel-system"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_REGION: str = "us-east-1"
    STORAGE_USE_SSL: bool = False
    EMAIL_PROVIDER: str = "mailpit"
    EMAIL_FROM: str = "Travel System <noreply@localhost>"
    RESEND_API_KEY: Optional[str] = None
    BASE_CURRENCY: str = "UGX"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

settings = Settings()
