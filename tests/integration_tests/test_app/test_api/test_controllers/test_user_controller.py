import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.models.main.user import User
from system.database.session import DatabaseSession
from system.database.settings import DatabaseId
from utils.assertions import assert_api_error_format
from utils.queries import execute_raw_queries
from utils.uuids import mock_uuid
import nacl.pwhash


class TestGetAll:
    ENDPOINT = "/api/v4/users"

    @pytest.fixture(scope="function", autouse=True)
    def reset_data(self):
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(session, "TRUNCATE TABLE main.user CASCADE")
            session.commit()

    def test_ok(self, client: TestClient):
        # Arrange
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(
                session,
                f"""INSERT INTO main.user (id, name, email, phone, address) 
                    VALUES ('{mock_uuid(1)}', 'test_user', 'test_email', 'test_phone', 'test_address'),
                           ('{mock_uuid(2)}', 'test_user2', 'test_email2', 'test_phone2', 'test_address2')""",
            )
            session.commit()

        # Act
        response = client.get(self.ENDPOINT)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": [
                {
                    "id": mock_uuid(1),
                    "name": "test_user",
                    "email": "test_email",
                    "phone": "test_phone",
                    "address": "test_address",
                },
                {
                    "id": mock_uuid(2),
                    "name": "test_user2",
                    "email": "test_email2",
                    "phone": "test_phone2",
                    "address": "test_address2",
                },
            ],
            "meta": {"count": 2},
        }

    def test_no_values(self, client: TestClient):
        # Arrange
        # Act
        response = client.get(self.ENDPOINT)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": [],
            "meta": {"count": 0},
        }


class TestGet:
    ENDPOINT = "/api/v4/users/{user_id}"

    @pytest.fixture(scope="function", autouse=True)
    def reset_data(self):
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(session, "TRUNCATE TABLE main.user CASCADE")
            session.commit()

    def test_ok(self, client: TestClient):
        # Arrange
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(
                session,
                f"""INSERT INTO main.user (id, name, email, phone, address) 
                            VALUES ('{mock_uuid(1)}', 'test_user', 'test_email', 'test_phone', 'test_address'),
                                   ('{mock_uuid(2)}', 'test_user2', 'test_email2', 'test_phone2', 'test_address2')""",
            )
            session.commit()

        # Act
        response = client.get(self.ENDPOINT.format(user_id=mock_uuid(1)))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "data": {
                "id": mock_uuid(1),
                "name": "test_user",
                "email": "test_email",
                "phone": "test_phone",
                "address": "test_address",
            },
        }

    def test_not_found(self, client: TestClient):
        # Arrange
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(
                session,
                f"""INSERT INTO main.user (id, name, email, phone, address) 
                            VALUES ('{mock_uuid(1)}', 'test_user', 'test_email', 'test_phone', 'test_address'),
                                   ('{mock_uuid(2)}', 'test_user2', 'test_email2', 'test_phone2', 'test_address2')""",
            )
            session.commit()

        # Act
        response = client.get(self.ENDPOINT.format(user_id=mock_uuid(3)))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert_api_error_format(response)


class TestCreate:
    ENDPOINT = "/api/v4/users"

    @pytest.fixture(scope="function", autouse=True)
    def reset_data(self):
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(session, "TRUNCATE TABLE main.user CASCADE")
            session.commit()

    def test_created(self, client: TestClient):
        # Arrange
        data = {
            "name": "test_user",
            "email": "test_email",
            "phone": "test_phone",
            "address": "test_address",
            "password": "test_password",
        }

        # Act
        response = client.post(self.ENDPOINT, json=data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        assert "data" in response.json()
        assert "id" in response.json()["data"]

        with DatabaseSession.get(DatabaseId.MAIN) as session:
            data = session.get(User, response.json()["data"]["id"])

        assert str(data.id) == response.json()["data"]["id"]
        assert data.name == "test_user"
        assert data.email == "test_email"
        assert data.phone == "test_phone"
        assert data.address == "test_address"
        assert nacl.pwhash.verify(data.password_hash.encode(), "test_password".encode())

    def test_missing_data(self, client: TestClient):
        # Arrange
        data = {
            "name": "test_user",
            "email": "test_email",
            "phone": "test_phone",
        }

        # Act
        response = client.post(self.ENDPOINT, json=data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert_api_error_format(response)

    def test_email_conflict(self, client: TestClient):
        # Arrange
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(
                session,
                f"""INSERT INTO main.user (id, name, email, phone, address) 
                            VALUES ('{mock_uuid(1)}', 'test_user', 'test_exisiting_email', 'test_phone', 'test_address')""",
            )
            session.commit()

        data = {
            "name": "test_user",
            "email": "test_exisiting_email",
            "phone": "test_phone",
            "address": "test_address",
            "password": "test_password",
        }

        # Act
        response = client.post(self.ENDPOINT, json=data)

        # Assert
        assert response.status_code == status.HTTP_409_CONFLICT
        assert_api_error_format(response)


class TestUpdate:
    ENDPOINT = "/api/v4/users/{user_id}"

    @pytest.fixture(scope="function", autouse=True)
    def reset_data(self):
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(session, "TRUNCATE TABLE main.user CASCADE")
            session.commit()

    def test_ok(self, client: TestClient):
        # Arrange
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(
                session,
                f"""INSERT INTO main.user (id, name, email, phone, address) 
                            VALUES ('{mock_uuid(1)}', 'test_user', 'test_email', 'test_phone', 'test_address'),
                                   ('{mock_uuid(2)}', 'test_user2', 'test_email2', 'test_phone2', 'test_address2')""",
            )
            session.commit()

        data = {
            "name": "test_user_updated",
            "phone": "test_phone_updated",
            "address": "test_address_updated",
        }

        # Act
        response = client.put(self.ENDPOINT.format(user_id=mock_uuid(1)), json=data)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.json()
        assert "id" in response.json()["data"]

        with DatabaseSession.get(DatabaseId.MAIN) as session:
            data = session.get(User, mock_uuid(1))

        assert str(data.id) == response.json()["data"]["id"]
        assert data.name == "test_user_updated"
        assert data.email == "test_email"
        assert data.phone == "test_phone_updated"
        assert data.address == "test_address_updated"

    def test_not_found(self, client: TestClient):
        # Arrange
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(
                session,
                f"""INSERT INTO main.user (id, name, email, phone, address) 
                            VALUES ('{mock_uuid(1)}', 'test_user', 'test_email', 'test_phone', 'test_address'),
                                   ('{mock_uuid(2)}', 'test_user2', 'test_email2', 'test_phone2', 'test_address2')""",
            )
            session.commit()

        data = {
            "name": "test_user_updated",
            "phone": "test_phone_updated",
            "address": "test_address_updated",
        }

        # Act
        response = client.put(self.ENDPOINT.format(user_id=mock_uuid(3)), json=data)

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert_api_error_format(response)

    def test_missing_data(self, client: TestClient):
        # Arrange
        data = {
            "name": "test_user",
            "email": "test_email",
            "phone": "test_phone",
        }

        # Act
        response = client.put(self.ENDPOINT.format(user_id=mock_uuid(1)), json=data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert_api_error_format(response)


class TestDelete:
    ENDPOINT = "/api/v4/users/{user_id}"

    @pytest.fixture(scope="function", autouse=True)
    def reset_data(self):
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(session, "TRUNCATE TABLE main.user CASCADE")
            session.commit()

    def test_ok(self, client: TestClient):
        # Arrange
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(
                session,
                f"""INSERT INTO main.user (id, name, email, phone, address) 
                            VALUES ('{mock_uuid(1)}', 'test_user', 'test_email', 'test_phone', 'test_address'),
                                   ('{mock_uuid(2)}', 'test_user2', 'test_email2', 'test_phone2', 'test_address2')""",
            )
            session.commit()

        # Act
        response = client.delete(self.ENDPOINT.format(user_id=mock_uuid(1)))

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.json()
        assert "id" in response.json()["data"]

        with DatabaseSession.get(DatabaseId.MAIN) as session:
            data = session.get(User, mock_uuid(1))

        assert data is None

    def test_not_found(self, client: TestClient):
        # Arrange
        with DatabaseSession.get(DatabaseId.MAIN) as session:
            _ = execute_raw_queries(
                session,
                f"""INSERT INTO main.user (id, name, email, phone, address) 
                            VALUES ('{mock_uuid(1)}', 'test_user', 'test_email', 'test_phone', 'test_address'),
                                   ('{mock_uuid(2)}', 'test_user2', 'test_email2', 'test_phone2', 'test_address2')""",
            )
            session.commit()

        # Act
        response = client.delete(self.ENDPOINT.format(user_id=mock_uuid(3)))

        # Assert
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert_api_error_format(response)
