from fastapi import APIRouter
from fastapi.responses import ORJSONResponse

from app.api.controllers.routes import v4_router

api_router = APIRouter(prefix="/api", default_response_class=ORJSONResponse)
api_router.include_router(v4_router)
