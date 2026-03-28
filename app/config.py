"""
NEX Ledger — Configuration management.
Uses Pydantic Settings for environment variable validation.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "postgresql+pg8000://ledger:ledger@localhost:9181/nex_ledger"
    TEST_DATABASE_URL: str = "postgresql+pg8000://ledger:ledger@localhost:9181/nex_ledger_test"
    SECRET_KEY: str = "change-this-in-production"
    APP_NAME: str = "nex-ledger"
    PORT: int = 9180
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "case_sensitive": False}


settings = Settings()
