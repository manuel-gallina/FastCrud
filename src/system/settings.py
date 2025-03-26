from functools import lru_cache
from typing import Tuple, Type

from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from system.authentication.settings import AuthSettings
from system.database.settings import DatabaseId, DatabaseSettings
from system.datetime.settings import DatetimeSettings
from system.logging.settings import LoggingSettings
from system.redis.settings import RedisSettings


class Settings(BaseSettings):
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls, "settings.yaml"),
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
    )

    @property
    def app_version(self) -> str:
        return "0.1.0"

    app_name: str
    redis: RedisSettings
    logging: LoggingSettings
    datetime: DatetimeSettings
    databases: dict[DatabaseId, DatabaseSettings]
    auth: AuthSettings


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore ; missing values are read from the environment


@lru_cache
def get_redis_settings() -> RedisSettings:
    return get_settings().redis


@lru_cache
def get_datetime_settings() -> DatetimeSettings:
    return get_settings().datetime


@lru_cache
def get_database_settings(database_id: DatabaseId) -> DatabaseSettings:
    return get_settings().databases[database_id]


@lru_cache
def get_logging_settings() -> LoggingSettings:
    return get_settings().logging


@lru_cache
def get_auth_settings() -> AuthSettings:
    return get_settings().auth
