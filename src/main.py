import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from h11 import LocalProtocolError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import ClientDisconnect

from app.api.routes import api_router
from app.api.schema.shared.errors import (
    ApiError,
    handle_api_error,
    handle_request_validation_error,
)
from system.logging.setup import init_logging
from system.settings import get_settings
from system.uuids import generate_uuid


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    logger = init_logging()

    logger.debug("Settings: %s", settings.model_dump_json(indent=2))
    logger.info("Starting %s", settings.app_name)
    yield
    logger.info("Stopping %s", settings.app_name)


fastapi_app = FastAPI(
    lifespan=lifespan,
    openapi_url=None,
)
fastapi_app.include_router(api_router)


@fastapi_app.exception_handler(Exception)
@fastapi_app.exception_handler(ApiError)
async def http_exception_handler(request: Request, exc: Exception):
    return await handle_api_error(request, exc)


@fastapi_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return handle_request_validation_error(request, exc)


@fastapi_app.middleware("http")
async def catch_cancelled_request(request: Request, call_next):
    try:
        return await call_next(request)
    except (ClientDisconnect, LocalProtocolError):
        return Response(status_code=status.HTTP_204_NO_CONTENT)


class SuppressNoResponseReturnedMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except RuntimeError as exc:
            if str(exc) == "No response returned." and await request.is_disconnected():
                request_logger = request.state.logger
                request_logger.info("Request cancelled")
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            raise


# noinspection PyTypeChecker
fastapi_app.add_middleware(SuppressNoResponseReturnedMiddleware)


@fastapi_app.middleware("http")
async def log_request(request: Request, call_next):
    request_logger = request.state.request_logger
    request_logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    request_logger.info(f"Response: {response.status_code}")
    return response


@fastapi_app.middleware("http")
async def set_request_logger(request: Request, call_next):
    request_id = request.state.request_id
    request_logger = logging.getLogger(request_id)
    request.state.request_logger = request_logger
    response = await call_next(request)
    return response


@fastapi_app.middleware("http")
async def set_request_id(request: Request, call_next):
    request_id = generate_uuid("REQ")
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@fastapi_app.middleware("http")
async def remove_content_type_on_204(request: Request, call_next):
    response = await call_next(request)
    if response.status_code == status.HTTP_204_NO_CONTENT:
        del response.headers["content-type"]
    return response
