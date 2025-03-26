from logging import Logger

import nacl.pwhash
from fastapi import APIRouter, status
from fastapi.params import Depends
from nacl.exceptions import InvalidkeyError
from sqlalchemy import Select
from sqlmodel import Session, select

from app.user.routes import user_router
from app.api.schema.auth_schema import (
    LoginRequest,
    LoginResponse,
    AuthSchema,
    TokensSchema,
    RefreshRequest,
    RefreshResponse,
)
from app.api.schema.shared.errors import ApiError
from app.user.schema import UserSchema
from app.core.models.main.device import Device
from app.core.models.main.user import User
from app.core.services import auth_service
from app.core.services.auth_service import (
    AuthService,
    TokenPayload,
    RefreshTokenPayload,
)
from system.database.session import DatabaseSession
from system.database.settings import DatabaseId
from system.logging.api_logger import get_request_logger, RequestLog

auth_router = APIRouter(prefix="/auth")


@auth_router.post("/login")
async def login(
    body: LoginRequest,
    logger: Logger = Depends(get_request_logger),
    main_database_session: Session = Depends(DatabaseSession(DatabaseId.MAIN)),
    auth_service: AuthService = Depends(),
) -> LoginResponse:
    logger.debug(RequestLog(input={"body": body}))

    user_query: Select = select(User).where(User.email == body.email)
    user: User | None = main_database_session.exec(user_query).first()
    if user is None:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            detail=f"User not found with email: {body.email}",
        )

    try:
        nacl.pwhash.verify(
            user.password_hash.encode(), body.password.get_secret_value().encode()
        )
    except InvalidkeyError as ex:
        raise ApiError(
            status_code=status.HTTP_401_UNAUTHORIZED, message="Invalid password"
        ) from ex

    access_token = auth_service.generate_access_token(TokenPayload(user_id=user.id))
    refresh_token = auth_service.generate_refresh_token(
        RefreshTokenPayload(user_id=user.id)
    )

    device_query: Select = select(Device).where(
        Device.user_id == user.id, Device.code == body.device_code
    )
    device = Device(user_id=user.id, code=body.device_code, refresh_token=refresh_token)
    main_database_session.add(device)

    return LoginResponse(
        data=AuthSchema(
            tokens=TokensSchema(access_token=access_token, refresh_token=refresh_token),
            user=UserSchema(
                id=user.id,
                email=user.email,
                address=user.address,
                name=user.name,
                phone=user.phone,
            ),
        )
    )


@auth_router.post("/logout")
async def logout():
    return {"message": "Logout successful"}


@auth_router.post("/refresh")
async def refresh(
    body: RefreshRequest,
    logger: Logger = Depends(get_request_logger),
    main_database_session: Session = Depends(DatabaseSession(DatabaseId.MAIN)),
    auth_service: AuthService = Depends(),
) -> RefreshResponse:
    return {"message": "Refresh successful"}
