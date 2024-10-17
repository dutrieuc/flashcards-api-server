import pytest_asyncio

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from flashcards_server.api import decks
from flashcards_server.database import User


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


def test_endpoints_are_protected(logged_out_client: TestClient):
    assert 401 == logged_out_client.get("/decks").status_code


def test_get_deck_logged_out(
    session: Session, logged_out_client: TestClient, chemistry_deck
):
    assert 401 == logged_out_client.get(f"/decks/{chemistry_deck.id}").status_code


def test_get_decks(session: Session, client: TestClient, chemistry_deck, biology_deck):
    response = client.get("/decks")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_deck(session: Session, client: TestClient, chemistry_deck):
    response = client.get(f"/decks/{chemistry_deck.id}")
    assert response.status_code == 200
    assert response.json()["name"] == chemistry_deck.name


def test_get_deck_not_owned(
    session: Session, another_client: TestClient, chemistry_deck
):
    response = another_client.get("/decks")
    assert response.status_code == 200
    assert len(response.json()) == 0

    response = another_client.get(f"/decks/{chemistry_deck.id}")
    assert response.status_code == 404


def test_create_deck(session: Session, client: TestClient, chemistry_deck):
    deck = decks.DeckCreate(
        name="New",
        description="new cards",
        algorithm="random",
        parameters={},
        tags=[],
    )
    response = client.post("/decks/", json=deck.model_dump())
    assert response.status_code == 200
    assert response.json()["name"] == deck.name


def test_patch_deck(session: Session, client: TestClient, chemistry_deck):
    deck_patch = decks.DeckPatch(name="Biochemistry")
    description = chemistry_deck.description
    response = client.patch(f"/decks/{chemistry_deck.id}", json=deck_patch.model_dump())
    assert response.status_code == 200
    assert response.json()["name"] == deck_patch.name

    response = client.get(f"/decks/{chemistry_deck.id}")
    assert response.status_code == 200
    assert response.json()["name"] == deck_patch.name
    assert response.json()["description"] == description


def test_patch_deck_not_owned(
    session: Session, another_client: TestClient, chemistry_deck
):
    deck_patch = decks.DeckPatch(name="Biochemistry")
    response = another_client.patch(
        f"/decks/{chemistry_deck.id}", json=deck_patch.model_dump()
    )
    assert response.status_code == 404


def test_delete_deck(session: Session, client: TestClient, chemistry_deck):
    response = client.delete(f"/decks/{chemistry_deck.id}")
    assert response.status_code == 200

    response = client.get(f"/decks/{chemistry_deck.id}")
    assert response.status_code == 404


def test_delete_deck_not_owned(
    session: Session, another_client: TestClient, chemistry_deck
):
    response = another_client.delete(f"/decks/{chemistry_deck.id}")
    assert response.status_code == 404


def test_delete_deck_logged_out(
    session: Session, logged_out_client: TestClient, chemistry_deck
):
    assert 401 == logged_out_client.delete(f"/decks/{chemistry_deck.id}").status_code
