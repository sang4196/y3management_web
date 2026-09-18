import pytest
from pydantic import ValidationError

from y3management.config import ConfigurationError, Settings, load_settings


def test_required_settings_are_not_defaulted() -> None:
    with pytest.raises(ConfigurationError, match="database_url, environment"):
        load_settings()


@pytest.mark.parametrize(
    "changes",
    [
        {"environment": "staging"},
        {"log_level": "trace"},
        {"db_connect_timeout_seconds": 0},
        {"db_pool_timeout_seconds": 0},
        {"db_statement_timeout_ms": 0},
        {"readiness_timeout_seconds": 0},
        {"database_url": "not-a-url"},
        {"database_url": "sqlite:///test.db"},
        {"database_url": "postgresql+psycopg://user:pass@remote:5432/other"},
        {"database_url": "postgresql+psycopg://y3management_test:x@127.0.0.1/y3management_test"},
        {
            "database_url": "postgresql+psycopg://y3management_test:x@127.0.0.1:55433/"
            "y3management_test?host=other"
        },
    ],
)
def test_invalid_settings(settings: Settings, changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(settings.model_dump() | changes)


def test_production_rejects_development_settings(settings: Settings) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(settings.model_dump() | {"environment": "production"})


@pytest.mark.parametrize("password", ["password", "changeme", "local-example-only"])
def test_production_rejects_example_password(password: str) -> None:
    with pytest.raises(ValidationError):
        Settings.model_validate(
            {
                "environment": "production",
                "database_url": f"postgresql+psycopg://app:{password}@db.invalid:5432/app",
            }
        )


def test_production_explicit_settings_do_not_connect() -> None:
    settings = Settings.model_validate(
        {
            "environment": "production",
            "database_url": "postgresql+psycopg://app:synthetic-test-value@db.invalid:5432/app",
        }
    )
    assert settings.environment == "production"


def test_error_and_repr_do_not_expose_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "sensitive-sentinel"
    monkeypatch.setenv("Y3_ENVIRONMENT", "test")
    monkeypatch.setenv("Y3_DATABASE_URL", f"invalid-{secret}")
    with pytest.raises(ConfigurationError) as failure:
        load_settings()
    assert secret not in str(failure.value)
    monkeypatch.setenv(
        "Y3_DATABASE_URL",
        f"postgresql+psycopg://y3management_test:{secret}@127.0.0.1:55433/y3management_test",
    )
    assert secret not in repr(load_settings())
