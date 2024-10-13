import uuid
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from flashcards_server.app import app
from flashcards_server.users import current_active_user
from flashcards_server.schemas import UserRead
from flashcards_core.database import init_db


user = UserRead(
    id=uuid.uuid4(),
    email="user@example.com",
    hashed_password="aaa",
    is_active=True,
    is_verified=True,
    is_superuser=False,
)


@pytest.fixture(name="session")
def session(tmpdir="/tmp"):
    session_maker = init_db(database_path=f"sqlite:///{tmpdir}/sqlite_test.db")
    with session_maker() as db:
        yield db


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app.dependency_overrides[current_active_user] = lambda: user
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(name="logged_out_client")
def logged_out_client_fixture(session: Session):
    with TestClient(app) as test_client:
        yield test_client
