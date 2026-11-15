from functools import lru_cache

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", hide_input_in_errors=True)

    app_env: str = "local"
    rabbitmq_url: SecretStr = SecretStr("")
    assistant_proposal_secret: SecretStr = SecretStr("local-only-proposal-secret-change-me")
    openrouter_api_key: SecretStr = SecretStr("")
    openrouter_primary_model: str = ""
    openrouter_fallback_model: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    enable_llm_test_fixture: bool = False
    assistant_max_concurrent: int = Field(default=2, ge=1, le=4)
    git_sha: str = "dev"
    release_version: str = "unreleased"

    @model_validator(mode="after")
    def safe_provider(self):
        fixture = (
            self.app_env == "local"
            and self.enable_llm_test_fixture
            and self.openrouter_primary_model == "test/scripted"
            and self.openrouter_api_key.get_secret_value() == "fixture-not-secret"
            and self.openrouter_base_url == "http://llm-fixture:8090/v1"
        )
        if self.openrouter_base_url != "https://openrouter.ai/api/v1" and not fixture:
            raise ValueError("Only the official HTTPS provider or the isolated test fixture is allowed")
        if self.enable_llm_test_fixture and not fixture:
            raise ValueError("Scripted LLM is allowed only in the isolated local test stack")
        secret = self.assistant_proposal_secret.get_secret_value()
        if self.app_env != "local" and (len(secret) < 32 or secret == "local-only-proposal-secret-change-me"):
            raise ValueError("Configure a separate proposal signing secret")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
