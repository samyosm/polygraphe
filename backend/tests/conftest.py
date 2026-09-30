import pytest
from fastapi.testclient import TestClient

from app.config import Settings, StorageBackend
from app.main import create_app
from app.storage.measurements import InMemoryRepository

TOKEN = "test-token"


@pytest.fixture
def repository() -> InMemoryRepository:
    return InMemoryRepository()


OPERATOR_PASSWORD = "operator-test-password"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        device_token=TOKEN,
        operator_password=OPERATOR_PASSWORD,
        storage_backend=StorageBackend.MEMORY,
        dummy_enabled=False,
    )


@pytest.fixture
def anonymous(settings: Settings):
    """A client that is not signed in: it may only watch."""
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture
def client(anonymous: TestClient):
    """A client signed in as operator."""
    token = anonymous.post("/auth/operator", json={"password": OPERATOR_PASSWORD}).json()["token"]
    anonymous.headers["Authorization"] = f"Bearer {token}"
    return anonymous
