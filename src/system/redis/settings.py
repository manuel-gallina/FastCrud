from pydantic import BaseModel, SecretStr


class RedisSettings(BaseModel):
    host: str
    port: int
    db: int
    username: str | None = None
    password: SecretStr | None = None
