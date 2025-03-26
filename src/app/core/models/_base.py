from uuid import UUID

import uuid6
from sqlmodel import SQLModel, Field


class BaseTable(SQLModel):
    id: UUID = Field(primary_key=True, default_factory=uuid6.uuid7)

    class Config:
        from_attributes = True
