from pydantic import BaseModel


class DatetimeSettings(BaseModel):
    timezone: str
