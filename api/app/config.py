from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Абсолютні шляхи до env-файлів (config.py = <root>/api/app/config.py):
#   _API_DIR  = parents[1] = <root>/api  — тека бекенду
#   _ROOT_DIR = parents[2] = <root>      — корінь монорепо
# Абсолютні шляхи потрібні, бо бекенд запускається з теки api/, а спільний
# .env лежить на корені (його ж читає docker-compose). У контейнері файлів за
# цими шляхами нема — pydantic тоді бере реальні env-змінні (їх дає compose).
_API_DIR = Path(__file__).resolve().parents[1]
_ROOT_DIR = Path(__file__).resolve().parents[2]


class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "db"
    user: str = "user"
    password: str = "pass"

    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @property
    def url(self) -> PostgresDsn:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def url_sync(self) -> PostgresDsn:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class TimeCampConfig(BaseModel):
    token: str = "<PASSWORD>"


class JiraConfig(BaseModel):
    token: str = "<PASSWORD>"


class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    # host-порт за конвенцією 10xxx (сервіси); db — 11xxx
    port: int = 10331
    jwt_secret: str = ""
    jwt_ttl_hours: int = 24
    cors_origins: Annotated[list[str], NoDecode] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors_origins(cls, value):
        if value is None or value == "":
            return ["*"]
        if isinstance(value, str):
            parts = [p.strip() for p in value.split(",") if p.strip()]
            return parts or ["*"]
        return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Джерела env за зростанням пріоритету (пізніші перекривають раніші);
        # реальні OS/compose env-змінні мають пріоритет над усіма файлами:
        #   1) api/.env.template — бекендні дефолти (комітиться)
        #   2) <root>/.env       — спільний конфіг (його ж читає docker-compose)
        #   3) api/.env          — локальний override розробника (якщо є; gitignore)
        env_file=(
            _API_DIR / ".env.template",
            _ROOT_DIR / ".env",
            _API_DIR / ".env",
        ),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP__",
        env_ignore_empty=True,
    )
    db: DatabaseConfig = DatabaseConfig()
    tc: TimeCampConfig = TimeCampConfig()
    jira: JiraConfig = JiraConfig()
    api: APIConfig = APIConfig()
    current_user: str = ''

    @model_validator(mode="after")
    def _require_jwt_secret_when_api_used(self) -> "Settings":
        # Fail fast if API is being used but no JWT secret is configured.
        # An empty default is allowed so CLI/notebook flows keep working when
        # the HTTP layer is not in play; the API entrypoint calls
        # ``require_api_ready`` explicitly before serving requests.
        return self

    def require_api_ready(self) -> None:
        if not self.api.jwt_secret:
            raise RuntimeError(
                "APP__API__JWT_SECRET is required to start the HTTP API. "
                "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
            )


settings = Settings()
