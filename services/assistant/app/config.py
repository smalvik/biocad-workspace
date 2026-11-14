from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_env: str = "local"
    booking_base_url: str = "http://booking:8000"
    openrouter_api_key: str = ""
    openrouter_primary_model: str = ""
    openrouter_fallback_model: str = ""
    git_sha: str = "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
