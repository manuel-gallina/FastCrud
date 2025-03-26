from uuid import UUID

from sqlmodel import Field

from app.core.models.main._base import MainTable


class Device(MainTable, table=True):
    user_id: UUID = Field(foreign_key="user.id")
    code: str
    refresh_token: str
