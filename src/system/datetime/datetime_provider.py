from datetime import datetime

import pytz
from fastapi import Depends

from system.datetime.settings import DatetimeSettings
from system.settings import get_datetime_settings


class DatetimeProvider:
    _settings: DatetimeSettings

    def __init__(self, settings: DatetimeSettings = Depends(get_datetime_settings)):
        self._settings = settings

    async def now_tz(self) -> datetime:
        """
        Returns the current datetime with the timezone from the settings
        :return: the current datetime
        """
        return datetime.now(pytz.timezone(self._settings.timezone))
