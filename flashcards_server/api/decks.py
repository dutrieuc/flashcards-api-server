from typing import List, Optional

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from flashcards_server.database import (
    get_async_session,
    Deck as DeckModel,
    Tag as TagModel,
)
from flashcards_server.users import current_active_user
from flashcards_server.schemas import UserRead
from flashcards_server.api.tags import TagRead, TagCreate


class DeckBase(BaseModel):
    name: str
    description: str
    algorithm: str


class DeckCreate(DeckBase):
    parameters: Optional[dict]
    tags: Optional[List[TagCreate]]


class DeckPatch(DeckCreate):
    name: Optional[str] = None
    description: Optional[str] = None
    algorithm: Optional[str] = None
    state: Optional[dict] = None
    parameters: Optional[dict] = None
    tags: Optional[List[TagCreate]] = None


class DeckRead(DeckBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parameters: dict
    state: dict
    tags: List[TagRead]


async def valid_deck(
    deck_id: UUID,
    user: UserRead,
    session: Session = Depends(get_async_session),
) -> DeckModel:
    """
    Check that the deck actually exists and belongs to the current user.

    :param deck_id: the ID of the deck to test.
    :returns: the deck object, if all checks passes.
    :raises: HTTPException is any check fails.
    """
    deck = await DeckModel.get_one(session=session, object_id=deck_id)
    if not deck or not await user.owns_deck(session=session, deck_id=deck_id):
        raise HTTPException(
            status_code=404, detail=f"Deck with ID '{deck_id}' not found"
        )
    return deck


router = APIRouter(
    prefix="/decks",
    tags=["decks"],
    # dependencies=[Depends(oauth2_scheme)],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=List[DeckRead])
async def get_my_decks(
    current_user: UserRead = Depends(current_active_user),
    session: Session = Depends(get_async_session),
):
    return await current_user.get_decks(session=session)


@router.get("/{deck_id}", response_model=DeckRead)
async def get_deck(
    deck_id: UUID,
    current_user: UserRead = Depends(current_active_user),
    session: Session = Depends(get_async_session),
):
    """
    Get all the details of a deck.

    :param deck_id: the id of the deck to get
    :returns: The details of the deck. Cards list not included, use ``/deck/<uuid>/cards``
    """
    return await valid_deck(session=session, user=current_user, deck_id=deck_id)


@router.post("/", response_model=DeckRead)
async def create_deck(
    deck: DeckCreate,
    current_user: UserRead = Depends(current_active_user),
    session: Session = Depends(get_async_session),
):
    """
    Creates a new deck with the given data.

    :param deck: the details of the new deck.
    :returns: The new deck
    """
    deck_data = deck.model_dump()
    tags = deck_data.pop("tags", [])
    new_deck: DeckModel = await current_user.create_deck(
        session=session, deck_data=deck_data
    )
    if tags:
        for tag in tags:
            tag_object = await session.run_sync(TagModel.get_by_name, name=tag["name"])
            if not tag_object:
                tag_object = await session.run_sync(TagModel.create, name=tag["name"])
            await session.run_sync(new_deck.assign_tag, tag_id=tag_object.id)

    return new_deck


@router.patch("/{deck_id}", response_model=DeckRead)
async def edit_deck(
    deck_id: UUID,
    new_deck_data: DeckPatch,
    current_user: UserRead = Depends(current_active_user),
    session: Session = Depends(get_async_session),
):
    """
    Edits the details of the given deck

    :param deck_id: the id of the deck to be modified
    :param new_deck_data: the new details of the deck. Can be partial.
    :returns: The modified deck. Cards list not included, use ``/deck/<uuid>/cards``
    """
    await valid_deck(session=session, user=current_user, deck_id=deck_id)
    update_data = new_deck_data.model_dump(exclude_none=True)
    tags = update_data.pop("tags", [])

    new_deck: DeckModel = await DeckModel.update_async(
        session=session, object_id=deck_id, **update_data
    )

    if tags:
        for tag in tags:
            tag_object = TagModel.get_by_name(session=session, name=tag["name"])
            if not tag_object:
                tag_object = TagModel.create(session=session, name=tag["name"])
            new_deck.assign_tag(session=session, tag_id=tag_object.id)

    return new_deck


@router.delete("/{deck_id}")
async def delete_deck(
    deck_id: UUID,
    current_user: UserRead = Depends(current_active_user),
    session: Session = Depends(get_async_session),
):
    """
    Removes the given deck

    :param deck_id: the id of the deck to remove
    :returns: None
    """
    await valid_deck(session=session, user=current_user, deck_id=deck_id)
    await current_user.delete_deck(session=session, deck_id=deck_id)
