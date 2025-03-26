from pydantic import BaseModel, SecretStr


class TokenSettings(BaseModel):
    secret: SecretStr
    lifetime_seconds: int
    payload_key: SecretStr


class AuthSettings(BaseModel):
    jwt_algorithm: str
    access_token: TokenSettings
    refresh_token: TokenSettings
