from uuid import UUID

from fastapi import Depends, HTTPException, Response, status
from gel import AsyncIOClient
from gel.errors import ConstraintViolationError

from nanapi.database.quizz.game_delete_by_message_id import (
    GameDeleteByMessageIdResult,
    game_delete_by_message_id,
)
from nanapi.database.quizz.game_end import GameEndResult, game_end
from nanapi.database.quizz.game_get_by_id import GameGetByIdResult, game_get_by_id
from nanapi.database.quizz.game_get_current import GameGetCurrentResult, game_get_current
from nanapi.database.quizz.game_get_last import GameGetLastResult, game_get_last
from nanapi.database.quizz.game_new import GameNewResult, game_new
from nanapi.database.quizz.game_select import GAME_SELECT_STATUS, GameSelectResult, game_select
from nanapi.database.quizz.game_update_bananed import GameUpdateBananedResult, game_update_bananed
from nanapi.database.quizz.quizz_delete_by_id import QuizzDeleteByIdResult, quizz_delete_by_id
from nanapi.database.quizz.quizz_get_by_id import QuizzGetByIdResult, quizz_get_by_id
from nanapi.database.quizz.quizz_get_oldest import QuizzGetOldestResult, quizz_get_oldest
from nanapi.database.quizz.quizz_insert import QuizzInsertResult, quizz_insert
from nanapi.database.quizz.quizz_set_answer import QuizzSetAnswerResult, quizz_set_answer
from nanapi.models.quizz import (
    EndGameBody,
    NewGameBody,
    NewQuizzBody,
    SetGameBananedAnswerBody,
    SetQuizzAnswerBody,
)
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/quizz', tags=['quizz'])


@router.oauth2_client_restricted.post(
    '/quizzes', response_model=QuizzInsertResult, status_code=status.HTTP_201_CREATED
)
async def new_quizz(body: NewQuizzBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Create a new quizz."""
    return await quizz_insert(edgedb, **body.model_dump())


@router.oauth2_client.get(
    '/quizzes/oldest',
    response_model=QuizzGetOldestResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_oldest_quizz(channel_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get the oldest quizz for a channel."""
    resp = await quizz_get_oldest(edgedb, channel_id=channel_id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client.get(
    '/quizzes/{id}',
    response_model=QuizzGetByIdResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_quizz(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get a quizz by ID."""
    resp = await quizz_get_by_id(edgedb, id=id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.delete(
    '/quizzes/{id}',
    response_model=QuizzDeleteByIdResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def delete_quizz(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a quizz by ID."""
    resp = await quizz_delete_by_id(edgedb, id=id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client_restricted.put(
    '/quizzes/{id}/answer',
    response_model=QuizzSetAnswerResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def set_quizz_answer(
    id: UUID, body: SetQuizzAnswerBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Set the answer for a quizz."""
    resp = await quizz_set_answer(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client.get('/games', response_model=list[GameSelectResult])
async def get_games(
    status: GAME_SELECT_STATUS, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get games by status."""
    return await game_select(edgedb, status=status)


@router.oauth2_client_restricted.post(
    '/games',
    response_model=GameNewResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel)},
)
async def new_game(body: NewGameBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Create a new game."""
    try:
        return await game_new(edgedb, **body.model_dump())
    except ConstraintViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.oauth2_client.get(
    '/games/current',
    response_model=GameGetCurrentResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_current_game(channel_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get the current game for a channel."""
    resp = await game_get_current(edgedb, channel_id=channel_id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client.get(
    '/games/last',
    response_model=GameGetLastResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_last_game(channel_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get the last game for a channel."""
    resp = await game_get_last(edgedb, channel_id=channel_id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.delete(
    '/games',
    response_model=GameDeleteByMessageIdResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def delete_game(message_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a game by message ID."""
    resp = await game_delete_by_message_id(edgedb, message_id=message_id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client.get(
    '/games/{id}',
    response_model=GameGetByIdResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_game(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get a game by ID."""
    resp = await game_get_by_id(edgedb, id=id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.put(
    '/games/{id}/bananed',
    response_model=GameUpdateBananedResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def set_game_bananed_answer(
    id: UUID, body: SetGameBananedAnswerBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Set the bananed answer for a game."""
    resp = await game_update_bananed(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.post(
    '/games/{id}/end',
    response_model=GameEndResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def end_game(
    id: UUID, body: EndGameBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """End a game by ID."""
    resp = await game_end(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp
