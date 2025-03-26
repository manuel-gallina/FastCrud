from enum import Enum

from pydantic import BaseModel, SecretStr


class DatabaseId(str, Enum):
    MAIN = "MAIN"


class DatabaseSettings(BaseModel):
    drivername: str
    username: str | None
    password: SecretStr | None
    host: str | None
    port: int | None
    database: str | None
    pool_size: int
    query: dict
