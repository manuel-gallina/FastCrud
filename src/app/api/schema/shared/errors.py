import http
import json
from logging import Logger

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app.api.schema.shared.base import BaseSchema


class _ApiErrorSchema(BaseSchema):
    request_id: str
    code: str
    message: str
    detail: str


class _ApiErrorResponseSchema(BaseSchema):
    error: _ApiErrorSchema


class ApiError(Exception):
    status_code: int
    """HTTP status code"""

    message: str
    """Error message. 
    Should not contain variable content, so that it can be easily translated."""

    detail: str
    """Error details.
    May contain additional variable content, useful for debugging."""

    def __init__(self, status_code: int, message: str, detail: str):
        """
        API error that will be returned to the client.

        :param status_code: HTTP status code
        :param message: Error message. Should not contain variable content, so that it can be easily translated.
        :param detail: Error details. May contain additional variable content, useful for debugging.
        """
        super().__init__(detail)
        self.status_code = status_code
        self.message = message
        self.detail = detail


async def handle_api_error(request: Request, exc: Exception) -> JSONResponse:
    logger: Logger = request.state.request_logger

    if isinstance(exc, ApiError):
        status_code = exc.status_code
        api_error = _ApiErrorSchema(
            request_id=request.state.request_id,
            code=http.HTTPStatus(status_code).phrase,
            message=exc.message,
            detail=exc.detail,
        )
    else:
        logger.error(exc)
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        api_error = _ApiErrorSchema(
            request_id=request.state.request_id,
            code=http.HTTPStatus(status_code).phrase,
            message=http.HTTPStatus(status_code).phrase,
            detail=str(exc),
        )

    return JSONResponse(
        content=_ApiErrorResponseSchema(error=api_error).model_dump(by_alias=True),
        status_code=status_code,
    )


def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    return JSONResponse(
        content=_ApiErrorResponseSchema(
            error=_ApiErrorSchema(
                code=http.HTTPStatus(status_code).phrase,
                detail=json.dumps(jsonable_encoder(exc.errors())),
                request_id=request.state.request_id,
                message="Validation error",
            )
        ).model_dump(by_alias=True),
        status_code=status_code,
    )
