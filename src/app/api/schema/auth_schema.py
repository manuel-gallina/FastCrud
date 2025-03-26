from pydantic import SecretStr

from app.api.schema.user_schema import UserSchema
from app.api.schema.shared.base import BaseSchema


class TokensSchema(BaseSchema):
    access_token: str
    refresh_token: str


class AuthSchema(BaseSchema):
    tokens: TokensSchema
    user: UserSchema


class LoginRequest(BaseSchema):
    email: str
    password: SecretStr


class LoginResponse(BaseSchema):
    data: AuthSchema


class RefreshRequest(BaseSchema):
    refresh_token: SecretStr


class RefreshResponse(LoginResponse):
    pass
