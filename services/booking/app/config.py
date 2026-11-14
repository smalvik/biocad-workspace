from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = "local"
    database_url: str = "postgresql+asyncpg://biocad:biocad@postgres:5432/biocad"
    session_secret: str = "dev-only-insecure-secret"
    display_tz: str = "Europe/Moscow"
    git_sha: str = "dev"
    seed_demo_data: bool = False
    demo_password: str = "demo-workspace"

    @model_validator(mode="after")
    def session_key_for_environment(self):
        if self.app_env != "local" and (
            len(self.session_secret) < 32 or self.session_secret == "dev-only-insecure-secret"
        ):
            raise ValueError("Configure a session secret of at least 32 characters outside local")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
