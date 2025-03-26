import pytest
from fastapi.testclient import TestClient

from main import fastapi_app
from system.settings import Settings


@pytest.fixture(scope="session")
def settings() -> Settings:
    # noinspection PyArgumentList
    return Settings()


@pytest.fixture(scope="session")
def client():
    with TestClient(fastapi_app) as client:
        yield client
