import uuid
import pytest
import pytest_asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from flashcards_server.app import app
from flashcards_server.users import current_active_user
from flashcards_server.database import User, get_async_session
from flashcards_core.database import Base

user = User(
    id=uuid.uuid4(),
    email="user@example.com",
    hashed_password="aaa",
    is_active=True,
    is_verified=True,
    is_superuser=False,
)

another_user = User(
    id=uuid.uuid4(),
    email="another_user@example.com",
    hashed_password="bbb",
    is_active=True,
    is_verified=True,
    is_superuser=False,
)


@pytest_asyncio.fixture(name="session", scope="function", autouse=False)
async def session(tmpdir="/tmp"):
    DATABASE_URL = f"sqlite+aiosqlite:///{tmpdir}/test.db"
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="user", scope="session")
def user_fixture():
    yield user


@pytest.fixture(scope="function")
def client(session: Session, user: User):
    app.dependency_overrides[current_active_user] = lambda: user
    app.dependency_overrides[get_async_session] = lambda: session

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def another_client(session: Session):
    app.dependency_overrides[current_active_user] = lambda: another_user
    app.dependency_overrides[get_async_session] = lambda: session

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides = {}


@pytest.fixture(name="logged_out_client")
def logged_out_client_fixture(session: Session):
    with TestClient(app) as test_client:
        yield test_client
