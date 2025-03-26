from logging import Logger

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, Select
from sqlmodel import select, Session

from app.api.schema.user_schema import (
    UserSchema,
    GetAllUsersResponse,
    GetUserResponse,
    CreateUserRequest,
    UpdateUserRequest,
)
from app.api.schema.shared.base import CountMeta
from app.api.schema.shared.errors import ApiError
from app.api.schema.shared.filtering import FilteringParams, get_filtering
from app.api.schema.shared.pagination import PaginationParams, get_pagination
from app.api.schema.shared.sorting import get_sorting, SortingParams
from app.core.identity import Identity, IdentityValidator
from app.core.models.main.user import User
from system.database.session import DatabaseSession
from system.database.settings import DatabaseId
from system.logging.api_logger import get_request_logger, RequestLog
import nacl.pwhash

user_router = APIRouter(prefix="/users")


@user_router.get("")
async def get_all(
    identity: Identity = Depends(IdentityValidator()),
    logger: Logger = Depends(get_request_logger),
    main_database_session: Session = Depends(DatabaseSession(DatabaseId.MAIN)),
    filtering: FilteringParams = Depends(get_filtering),
    sorting: SortingParams = Depends(get_sorting),
    pagination: PaginationParams = Depends(get_pagination(100, 300)),
) -> GetAllUsersResponse:
    logger.debug(
        RequestLog(
            input={
                "filtering": filtering,
                "sorting": sorting,
                "pagination": pagination,
            },
            identity=identity,
        )
    )

    data = main_database_session.exec(
        UserSchema.build_query(
            select(User),
            pagination.skip,
            pagination.limit,
            filtering.where,
            sorting.order_by,
        )
    ).all()

    count = main_database_session.exec(
        UserSchema.build_query(
            select(func.count(User.id)),
            where=filtering.where,
        )
    ).one()

    return GetAllUsersResponse(
        data=[
            UserSchema(
                id=d.id,
                name=d.name,
                email=d.email,
                phone=d.phone,
                address=d.address,
            )
            for d in data
        ],
        meta=CountMeta(
            count=count,
        ),
    )


@user_router.get("/{user_id}")
async def get(
    user_id: str,
    logger: Logger = Depends(get_request_logger),
    main_database_session: Session = Depends(DatabaseSession(DatabaseId.MAIN)),
) -> GetUserResponse:
    logger.debug(RequestLog(input={"user_id": user_id}))

    data = main_database_session.get(User, user_id)
    if not data:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            detail=f"User not found with id: {user_id}",
        )

    return GetUserResponse(
        data=UserSchema(
            id=data.id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            address=data.address,
        )
    )


@user_router.post("", status_code=status.HTTP_201_CREATED)
async def create(
    body: CreateUserRequest,
    logger: Logger = Depends(get_request_logger),
    main_database_session: Session = Depends(DatabaseSession(DatabaseId.MAIN)),
) -> GetUserResponse:
    logger.debug(RequestLog(input={"body": body}))

    data_query: Select = select(User).where(User.email == body.email)
    data = main_database_session.exec(data_query).first()
    if data:
        raise ApiError(
            status_code=status.HTTP_409_CONFLICT,
            message="User already exists",
            detail=f"User already exists with email: {body.email}",
        )

    data = User(
        name=body.name,
        email=body.email,
        phone=body.phone,
        address=body.address,
        password_hash=nacl.pwhash.str(body.password.encode()).decode(),
    )
    main_database_session.add(data)

    return GetUserResponse(
        data=UserSchema(
            id=data.id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            address=data.address,
        )
    )


@user_router.put("/{user_id}")
async def update(
    user_id: str,
    body: UpdateUserRequest,
    logger: Logger = Depends(get_request_logger),
    main_database_session: Session = Depends(DatabaseSession(DatabaseId.MAIN)),
) -> GetUserResponse:
    logger.debug(RequestLog(input={"user_id": user_id, "body": body}))

    data = main_database_session.get(User, user_id)
    if not data:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            detail=f"User not found with id: {user_id}",
        )

    data.name = body.name
    data.phone = body.phone
    data.address = body.address

    return GetUserResponse(
        data=UserSchema(
            id=data.id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            address=data.address,
        )
    )


@user_router.delete("/{user_id}")
async def delete(
    user_id: str,
    logger: Logger = Depends(get_request_logger),
    main_database_session: Session = Depends(DatabaseSession(DatabaseId.MAIN)),
) -> GetUserResponse:
    logger.debug(RequestLog(input={"user_id": user_id}))

    data = main_database_session.get(User, user_id)
    if not data:
        raise ApiError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            detail=f"User not found with id: {user_id}",
        )

    main_database_session.delete(data)

    return GetUserResponse(
        data=UserSchema(
            id=data.id,
            name=data.name,
            email=data.email,
            phone=data.phone,
            address=data.address,
        )
    )
