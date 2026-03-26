"""Application configuration using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql+pg8000://nex_ledger:dev_password@localhost:5432/nex_ledger"
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    PORT: int = 9180
    ENV: str = "development"
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
