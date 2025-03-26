from fastapi import APIRouter

from app.api.controllers.auth_controller import auth_router
from app.api.controllers.user_controller import user_router
from app.api.controllers.server_info_controller import server_info_router

v4_router = APIRouter(prefix="/v4")
v4_router.include_router(server_info_router)
v4_router.include_router(user_router)
v4_router.include_router(auth_router)
