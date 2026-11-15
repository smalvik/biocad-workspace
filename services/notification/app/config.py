from urllib.parse import urlsplit

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore", hide_input_in_errors=True)
    rabbitmq_url: SecretStr = SecretStr("amqp://biocad:biocad-local@rabbitmq:5672/")
    notification_state_path: str = "/data/deliveries.sqlite"
    notification_public_url: str = "http://localhost:8080"
    mailpit_smtp_host: str = "mailpit"
    mailpit_smtp_port: int = Field(default=1025, ge=1, le=65535)
    smtp_timeout: float = Field(default=5, ge=0.1, le=10)
    git_sha: str = "dev"
    release_version: str = "unreleased"

    @model_validator(mode="after")
    def demo_only(self):
        if self.mailpit_smtp_host not in {"mailpit", "localhost", "127.0.0.1"}:
            raise ValueError("Only the private demo Mailpit SMTP sink is supported")
        url = urlsplit(self.notification_public_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in {"", "/"}
        ):
            raise ValueError("Expected a bare application HTTP(S) origin")
        return self
