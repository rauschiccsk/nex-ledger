"""Application configuration using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql+pg8000://ledger:ledger@localhost:5432/nex_ledger"
    PORT: int = 9180
    ENV: str = "development"
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
