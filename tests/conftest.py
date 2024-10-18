import uuid
import pytest
import pytest_asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from flashcards_core.database import Base

from flashcards_server.app import app
from flashcards_server.users import current_active_user
from flashcards_server.database import User, get_async_session
from flashcards_server.api import cards, decks, facts


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


@pytest_asyncio.fixture(name="biology_deck", scope="function")
async def biology_deck(session: Session, user: User):
    deck_1 = decks.DeckCreate(
        name="Biology",
        description="biology cards",
        algorithm="random",
        parameters={},  # TODO test with values, make optionnal
        tags=[],
    )
    return await decks.create_deck(deck=deck_1, current_user=user, session=session)


@pytest_asyncio.fixture(name="chemistry_deck", scope="function")
async def chemistry_deck(session: Session, user: User):
    deck_2 = decks.DeckCreate(
        name="Chemistry",
        description="Chemistry cards",
        algorithm="random",
        parameters={},
        tags=[],
    )
    return await decks.create_deck(deck=deck_2, current_user=user, session=session)


@pytest_asyncio.fixture(scope="function")
async def fact(session: Session, user: User):
    return await facts.create_fact(
        fact=facts.FactCreate(
            value="Oxygen",
            format="format",
            related=None,
            tags=[],
        ),
        current_user=user,
        session=session,
    )


@pytest_asyncio.fixture(scope="function")
async def fact_carbon(session: Session, user: User):
    return await facts.create_fact(
        fact=facts.FactCreate(
            value="carbon",
            format="format",
            related=[],
            tags=[],
        ),
        current_user=user,
        session=session,
    )


@pytest_asyncio.fixture(scope="function")
async def oxygen_card(session: Session, user: User, chemistry_deck, fact):
    return await cards.create_card(
        card=cards.CardCreate(
            question_id=fact.id,
            answer_id=fact.id,
            question_context_facts=[],
            answer_context_facts=[],
            tags=[],
        ),
        deck_id=chemistry_deck.id,
        current_user=user,
        session=session,
    )


@pytest_asyncio.fixture(scope="function")
async def carbon_card(session: Session, user: User, chemistry_deck, fact):
    return await cards.create_card(
        card=cards.CardCreate(
            question_id=fact.id,
            answer_id=fact.id,
            question_context_facts=[],
            answer_context_facts=[],
            tags=[],
        ),
        deck_id=chemistry_deck.id,
        current_user=user,
        session=session,
    )


@pytest_asyncio.fixture(scope="function")
async def chemistry_cards(session: Session, user: User, carbon_card, oxygen_card):
    return [carbon_card, oxygen_card]
