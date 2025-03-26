from app.api.schema.shared.base import BaseSchema


class ServerInfoResponse(BaseSchema):
    app_name: str
    app_version: str
    current_datetime: str


class GetServerInfoResponse(BaseSchema):
    data: ServerInfoResponse
