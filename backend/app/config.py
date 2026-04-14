from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://phonoteka:phonoteka_pass@localhost:5432/phonoteka"
    DATABASE_SYNC_URL: str = "postgresql://phonoteka:phonoteka_pass@localhost:5432/phonoteka"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_AUDIO: str = "audio"
    MINIO_BUCKET_COVERS: str = "covers"
    MINIO_SECURE: bool = False

    # JWT
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Claude API
    CLAUDE_API_KEY: str = "mock"
    CLAUDE_MODEL: str = "claude-sonnet-4-6"

    # Groq API
    GROQ_API_KEY: str = "mock"

    # ML Worker
    ML_WORKER_URL: str = "http://localhost:8001"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:80"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()
