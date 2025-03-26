from fastapi import APIRouter, Depends

from app.api.schema.server_info_schema import GetServerInfoResponse, ServerInfoResponse
from system.datetime.datetime_provider import DatetimeProvider
from system.settings import get_settings, Settings

server_info_router = APIRouter(prefix="/server-info")


@server_info_router.get("")
async def get(
    settings: Settings = Depends(get_settings),
    datetime_provider: DatetimeProvider = Depends(),
) -> GetServerInfoResponse:
    # Parse
    # Fetch / Process
    app_version = settings.app_version
    app_name = settings.app_name
    current_datetime = await datetime_provider.now_tz()

    # Format
    return GetServerInfoResponse(
        data=ServerInfoResponse(
            app_version=app_version,
            app_name=app_name,
            current_datetime=current_datetime.isoformat(),
        )
    )
