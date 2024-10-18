from fastapi.testclient import TestClient
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from flashcards_server.api import cards


def test_get_cards_logged_out(
    session: Session, logged_out_client: TestClient, chemistry_deck
):
    assert 401 == logged_out_client.get(f"/decks/{chemistry_deck.id}/cards").status_code


def test_get_cards(
    session: Session, client: TestClient, chemistry_deck, chemistry_cards
):
    response = client.get(f"/decks/{chemistry_deck.id}/cards")
    assert response.status_code == 200
    assert len(response.json()) == len(chemistry_cards)


def test_get_cards_not_owned(
    session: Session, another_client: TestClient, chemistry_deck
):
    response = another_client.get(f"/decks/{chemistry_deck.id}/cards")
    assert response.status_code == 404


def test_create_card(session: Session, client: TestClient, chemistry_deck, fact):
    card = cards.CardCreate(
        question_id=fact.id,
        answer_id=fact.id,
        question_context_facts=[],
        answer_context_facts=[],
        tags=[],
    )

    response = client.post(
        f"/decks/{chemistry_deck.id}/cards", json=jsonable_encoder(card)
    )
    assert response.status_code == 200
    assert response.json()["question"]["id"] == str(card.question_id)

    response = client.get(f"/decks/{chemistry_deck.id}/cards")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_patch_card(
    session: Session, client: TestClient, chemistry_deck, carbon_card, fact_carbon
):
    card_patch = cards.CardPatch(answer_id=fact_carbon.id)
    response = client.patch(
        f"/decks/{chemistry_deck.id}/cards/{carbon_card.id}",
        json=jsonable_encoder(card_patch),
    )
    assert response.status_code == 200
    assert response.json()["answer"]["id"] == str(fact_carbon.id)

    response = client.get(f"/decks/{chemistry_deck.id}/cards/{carbon_card.id}")
    assert response.status_code == 200
    assert response.json()["answer"]["id"] == str(fact_carbon.id)


def test_patch_card_not_owned(
    session: Session,
    another_client: TestClient,
    chemistry_deck,
    carbon_card,
    fact_carbon,
):
    card_patch = cards.CardPatch(answer_id=fact_carbon.id)
    response = another_client.patch(
        f"/decks/{chemistry_deck.id}/cards/{carbon_card.id}",
        json=jsonable_encoder(card_patch),
    )
    assert response.status_code == 404


def test_delete_card(session: Session, client: TestClient, chemistry_deck, carbon_card):
    response = client.delete(f"/decks/{chemistry_deck.id}/cards/{carbon_card.id}")
    assert response.status_code == 200

    response = client.get(f"/decks/{chemistry_deck.id}/cards/{carbon_card.id}")
    assert response.status_code == 404


def test_delete_card_not_owned(
    session: Session, another_client: TestClient, chemistry_deck, carbon_card
):
    response = another_client.delete(
        f"/decks/{chemistry_deck.id}/cards/{carbon_card.id}"
    )
    assert response.status_code == 404


def test_delete_card_logged_out(
    session: Session, logged_out_client: TestClient, chemistry_deck, carbon_card
):
    assert (
        401
        == logged_out_client.delete(
            f"/decks/{chemistry_deck.id}/cards/{carbon_card.id}"
        ).status_code
    )
