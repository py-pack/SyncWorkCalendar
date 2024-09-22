from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),  # порядок підвантаження мержа змінинних
        case_sensitive=False,  # не важливий регістр
        env_nested_delimiter="__",  # розділювач
        env_prefix="APP__",  # префікс змінних, які будуть автоматично парситись
        env_ignore_empty=True,  # ігнорувати пусті значення
    )
    db: DatabaseConfig = DatabaseConfig()
    tc: TimeCampConfig = TimeCampConfig()
    jira: JiraConfig = JiraConfig()
    current_user: str = ''
    templates: dict[str, list[str]] = {
        "MP-1": [
            "Daily stand-up",
        ],
        "MP-2": [
            "Grooming",
        ]
    }


settings = Settings()
