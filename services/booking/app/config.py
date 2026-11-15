from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", hide_input_in_errors=True)

    app_env: str = "local"
    database_url: str = "postgresql+asyncpg://biocad:biocad@postgres:5432/biocad"
    session_secret: str = "dev-only-insecure-secret"
    display_tz: str = "Europe/Moscow"
    git_sha: str = "dev"
    release_version: str = "unreleased"
    seed_demo_data: bool = False
    demo_password: str = "demo-workspace"
    rabbitmq_url: SecretStr = SecretStr("")
    assistant_budget_usd: float = Field(default=0, ge=0, le=1000)
    assistant_free_only: bool = True
    assistant_budget_epoch: str = Field(default="demo-v1", pattern=r"^[a-zA-Z0-9._-]{1,64}$")
    assistant_requests_per_minute: int = Field(default=3, ge=1, le=1000)

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
