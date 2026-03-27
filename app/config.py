"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "postgresql+pg8000://ledger:ledger@localhost:9181/nex_ledger"
    test_database_url: str = "postgresql+pg8000://ledger:ledger@localhost:9181/nex_ledger_test"
    secret_key: str = "change-this-in-production"
    port: int = 9180
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
