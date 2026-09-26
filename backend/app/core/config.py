from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"
    database_path: str = ".data/steezy.sqlite3"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="STEEZY_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
