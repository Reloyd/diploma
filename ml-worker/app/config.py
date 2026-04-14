from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://phonoteka:phonoteka_pass@localhost:5432/phonoteka"
    DATABASE_SYNC_URL: str = "postgresql://phonoteka:phonoteka_pass@localhost:5432/phonoteka"
    REDIS_URL: str = "redis://localhost:6379/0"
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin123"
    MINIO_BUCKET_AUDIO: str = "audio"
    MINIO_SECURE: bool = False
    ML_MODEL_VERSION: str = "v1"
    AUDIO_TMP_DIR: str = "/tmp/audio"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
