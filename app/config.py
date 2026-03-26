"""Application configuration using Pydantic BaseSettings"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    DATABASE_URL: str = "postgresql+pg8000://ledger:ledger@localhost:5432/nex_ledger"

    # Server
    PORT: int = 9180
    HOST: str = "0.0.0.0"

    # Environment
    ENV: str = "development"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:9180"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
