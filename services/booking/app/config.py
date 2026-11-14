from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+asyncpg://biocad:biocad@postgres:5432/biocad"
    session_secret: str = "dev-only-insecure-secret"
    display_tz: str = "Europe/Moscow"
    git_sha: str = "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
