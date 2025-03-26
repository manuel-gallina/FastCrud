import json
from datetime import datetime, timezone, timedelta
from uuid import UUID

import jwt
import nacl.secret
from binascii import unhexlify, hexlify
from fastapi.params import Depends
from pydantic import BaseModel

from system.authentication.settings import AuthSettings, TokenSettings
from system.settings import get_auth_settings


class AccessTokenPayload(BaseModel):
    user_id: UUID


class RefreshTokenPayload(AccessTokenPayload):
    pass


class AuthService:
    _settings: AuthSettings

    def __init__(self, settings: AuthSettings = Depends(get_auth_settings)):
        self._settings = settings

    def generate_access_token(self, payload: AccessTokenPayload) -> str:
        return self._generate_token(self._settings.access_token, payload)

    def generate_refresh_token(self, payload: RefreshTokenPayload) -> str:
        return self._generate_token(self._settings.refresh_token, payload)

    def _generate_token(
        self,
        token_settings: TokenSettings,
        payload: AccessTokenPayload | RefreshTokenPayload,
    ) -> str:
        encrypted_payload = hexlify(
            nacl.secret.Aead(
                unhexlify(token_settings.payload_key.get_secret_value().encode())
            ).encrypt(payload.model_dump_json().encode())
        ).decode()
        encoded = jwt.encode(
            {
                "exp": datetime.now(tz=timezone.utc)
                + timedelta(seconds=token_settings.lifetime_seconds),
                "payload": encrypted_payload,
            },
            token_settings.secret.get_secret_value(),
            self._settings.jwt_algorithm,
        )
        return encoded

    def validate_access_token(self, token: str) -> AccessTokenPayload:
        return AccessTokenPayload.model_validate(
            self._validate_token(self._settings.access_token, token)
        )

    def validate_refresh_token(self, token: str) -> RefreshTokenPayload:
        return RefreshTokenPayload.model_validate(
            self._validate_token(self._settings.refresh_token, token)
        )

    def _validate_token(self, token_settings: TokenSettings, token: str) -> dict:
        decoded = jwt.decode(
            token,
            token_settings.secret.get_secret_value(),
            algorithms=[self._settings.jwt_algorithm],
        )
        payload = (
            nacl.secret.Aead(
                unhexlify(token_settings.payload_key.get_secret_value().encode())
            )
            .decrypt(unhexlify(decoded["payload"]))
            .decode()
        )
        return json.loads(payload)
