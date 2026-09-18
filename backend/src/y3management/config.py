"""External settings only; no implicit development or production database."""

from typing import Literal, Self

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class ConfigurationError(ValueError):
    """Safe startup error without input values or credentials."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="Y3_",
        env_file=None,
        extra="ignore",
        hide_input_in_errors=True,
        frozen=True,
    )
    environment: Literal["development", "test", "production"]
    database_url: SecretStr = Field(repr=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    db_connect_timeout_seconds: int = Field(default=3, ge=2, le=30)
    db_pool_timeout_seconds: float = Field(default=2, gt=0, le=30)
    db_statement_timeout_ms: int = Field(default=2000, ge=100, le=30000)
    readiness_timeout_seconds: float = Field(default=4, gt=0, le=30)

    @model_validator(mode="after")
    def validate_database(self) -> Self:
        try:
            url = make_url(self.database_url.get_secret_value())
            port = url.port
        except Exception:
            raise ValueError("Invalid database connection configuration") from None
        if (
            url.drivername != "postgresql+psycopg"
            or not url.host
            or not url.database
            or not url.username
            or not url.password
            or port is None
            or not 1 <= port <= 65535
            or "," in url.host
            or set(url.query) - {"sslmode", "sslrootcert"}
        ):
            raise ValueError("A single explicit PostgreSQL psycopg target is required")
        if self.environment in {"development", "test"}:
            suffix = "dev" if self.environment == "development" else "test"
            expected = f"y3management_{suffix}"
            if (
                url.host not in {"127.0.0.1", "::1", "localhost"}
                or url.database != expected
                or url.username != expected
            ):
                raise ValueError("Use the dedicated local database and role for this environment")
        elif (
            url.database in {"y3management_dev", "y3management_test"}
            or url.username in {"y3management_dev", "y3management_test"}
            or url.password.lower() in {"password", "postgres", "changeme"}
            or "example" in url.password.lower()
        ):
            raise ValueError("Production must not use development or example credentials")
        return self


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        fields = sorted(
            {
                str(error["loc"][0]) if error["loc"] else "database"
                for error in exc.errors(include_input=False, include_context=False)
            }
        )
        raise ConfigurationError("Invalid settings: " + ", ".join(fields)) from None
