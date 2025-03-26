from fastapi import Request, Depends, status
from jwt import ExpiredSignatureError, DecodeError
from pydantic import BaseModel
from pydantic import SecretStr
from sqlmodel import Session

from app.api.schema.shared.errors import ApiError
from app.core.models.main.user import User
from app.core.services.auth_service import AuthService
from system.database.session import DatabaseSession
from system.database.settings import DatabaseId


class Identity(BaseModel):
    user: User | None
    is_system: bool
    access_token: SecretStr | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.is_system or self.user is not None


ANONYMOUS_IDENTITY = Identity(user=None, is_system=False)
SYSTEM_IDENTITY = Identity(user=None, is_system=True)


# Separating the get_identity function from the require_user_authentication function
# allows for better testability of the get_identity function.
def _get_authorization_header(request: Request) -> str | None:
    return request.headers.get("Authorization")


class IdentityValidator:
    _allow_anonymous: bool
    _roles: set[str] | None

    def __init__(self, *, allow_anonymous: bool = False, roles: set[str] | None = None):
        self._allow_anonymous = allow_anonymous
        self._roles = roles

    def __call__(
        self,
        authorization_header: str | None = Depends(_get_authorization_header),
        main_database_session: Session = Depends(DatabaseSession(DatabaseId.MAIN)),
        auth_service: AuthService = Depends(),
    ) -> Identity:
        if authorization_header is None:
            return self._get_anonymous_identity()
        token_parts = authorization_header.split(" ")
        if len(token_parts) != 2 or token_parts[0].lower() != "bearer":
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid authentication",
                detail="Invalid access token format",
            )
        access_token = token_parts[1]

        try:
            payload = auth_service.validate_access_token(access_token)
        except ExpiredSignatureError as ex:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid authentication",
                detail="Access token has expired",
            ) from ex
        except DecodeError as ex:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid authentication",
                detail="Invalid access token",
            ) from ex

        user: User | None = main_database_session.get(User, payload.user_id)
        if user is None:
            return self._get_anonymous_identity()

        return Identity(
            user=user,
            is_system=False,
            access_token=SecretStr(access_token),
        )

    def _get_anonymous_identity(self) -> Identity:
        if self._allow_anonymous:
            return ANONYMOUS_IDENTITY
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Invalid authentication",
            detail="Authentication required",
        )
