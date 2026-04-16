from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "async-messenger"
    app_env: str = "dev"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "messenger"
    db_user: str = "postgres"
    db_password: str = "postgres"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    media_root: str = "media"
    log_level: str = "info"
    log_path: str | None = None
    admin_username: str | None = Field(default=None, alias="ADMIN_USERNAME")
    admin_email: str | None = Field(default=None, alias="ADMIN_EMAIL")
    admin_password: str | None = Field(default=None, alias="ADMIN_PASSWORD")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True
    )

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
