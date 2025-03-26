from redis.asyncio import Redis
from fastapi import Depends

from system.redis.settings import RedisSettings
from system.settings import get_redis_settings


async def get_redis_connection(
    settings: RedisSettings = Depends(get_redis_settings),
) -> Redis:
    """
    Get a Redis connection using the provided settings, injectable as a FastAPI dependency.
    :param settings:
    :return:
    """
    async with build_redis_connection(settings) as redis_connection:
        yield redis_connection


def build_redis_connection(settings: RedisSettings | None = None) -> Redis:
    """
    Build a Redis connection using the provided settings, for usage outside FastAPI endpoints.
    :param settings:
    :return:
    """
    settings = settings or get_redis_settings()
    return Redis(
        protocol=3,
        host=settings.host,
        port=settings.port,
        db=settings.db,
        username=settings.username,
        password=(settings.password.get_secret_value() if settings.password else None),
    )
