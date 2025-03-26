from fastapi import status
from fastapi.testclient import TestClient
from freezegun import freeze_time

from system.settings import Settings


class TestGet:
    ENDPOINT = "/api/v4/server-info"

    def test_ok(self, client: TestClient, settings: Settings):
        # Arrange
        current_datetime = "2025-01-31T14:12:53.965608+01:00"
        app_version = settings.app_version
        app_name = settings.app_name

        # Act
        with freeze_time(current_datetime):
            response = client.get(self.ENDPOINT)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {
                "appName": app_name,
                "appVersion": app_version,
                "currentDatetime": current_datetime,
            }
        }
