from sqlalchemy import Engine, URL
from sqlmodel import create_engine, Session

from system.database.settings import (
    DatabaseId,
    DatabaseSettings,
)
from system.settings import get_database_settings, get_settings

_settings = get_settings()

_main_database_settings: DatabaseSettings = get_database_settings(DatabaseId.MAIN)
_main_database_connection_string = URL.create(
    _main_database_settings.drivername,
    username=_main_database_settings.username,
    password=_main_database_settings.password.get_secret_value(),
    host=_main_database_settings.host,
    port=_main_database_settings.port,
    database=_main_database_settings.database,
    query=_main_database_settings.query | {"application_name": _settings.app_name},
)


_database_engines: dict[DatabaseId, Engine] = {
    DatabaseId.MAIN: create_engine(
        _main_database_connection_string,
        logging_name=DatabaseId.MAIN,
        pool_size=_main_database_settings.pool_size,
        pool_pre_ping=True,
    ),
}


def get_database_engine(database_id: DatabaseId) -> Engine:
    return _database_engines[database_id]


class DatabaseSession:
    database_id: DatabaseId

    def __init__(self, database_id: DatabaseId):
        self.database_id = database_id

    def __call__(self) -> Session:
        engine = _database_engines[self.database_id]
        with Session(engine) as database_session:
            try:
                yield database_session
                database_session.commit()
            except Exception as e:
                database_session.rollback()
                raise e

    @staticmethod
    def get(database_id: DatabaseId) -> Session:
        engine = _database_engines[database_id]
        return Session(engine)
