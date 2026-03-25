from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    TENANT_ID: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
