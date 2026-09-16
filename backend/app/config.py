from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SatQuery AI Backend"
    APP_VERSION: str = "1.0.0"
    DATABASE_URL: str = "postgresql://satquery:satquery@localhost:5432/satquery"
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    FRONTEND_URL: str = "http://localhost:5173"
    AI_MODE: str = "real"
    MODEL_PATH: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
