from uuid import UUID

from fastapi import Depends, HTTPException, Response, status
from gel import AsyncIOClient

from nanapi.database.projection.projo_add_event import ProjoAddEventResult, projo_add_event
from nanapi.database.projection.projo_add_external_media import (
    ProjoAddExternalMediaResult,
    projo_add_external_media,
)
from nanapi.database.projection.projo_add_media import ProjoAddMediaResult, projo_add_media
from nanapi.database.projection.projo_delete import ProjoDeleteResult, projo_delete
from nanapi.database.projection.projo_delete_upcoming_events import (
    ProjoDeleteUpcomingEventsResult,
    projo_delete_upcoming_events,
)
from nanapi.database.projection.projo_insert import ProjoInsertResult, projo_insert
from nanapi.database.projection.projo_participant_add import (
    ProjoParticipantAddResult,
    projo_participant_add,
)
from nanapi.database.projection.projo_participant_remove import (
    ProjoParticipantRemoveResult,
    projo_participant_remove,
)
from nanapi.database.projection.projo_remove_external_media import (
    ProjoRemoveExternalMediaResult,
    projo_remove_external_media,
)
from nanapi.database.projection.projo_remove_media import (
    ProjoRemoveMediaResult,
    projo_remove_media,
)
from nanapi.database.projection.projo_select import (
    PROJO_SELECT_STATUS,
    ProjoSelectResult,
    projo_select,
)
from nanapi.database.projection.projo_update_message_id import (
    ProjoUpdateMessageIdResult,
    projo_update_message_id,
)
from nanapi.database.projection.projo_update_name import ProjoUpdateNameResult, projo_update_name
from nanapi.database.projection.projo_update_status import (
    ProjoUpdateStatusResult,
    projo_update_status,
)
from nanapi.models.common import ParticipantAddBody
from nanapi.models.projection import (
    NewProjectionBody,
    ProjoAddExternalMediaBody,
    SetProjectionMessageIdBody,
    SetProjectionNameBody,
    SetProjectionStatusBody,
)
from nanapi.utils.anilist import fetch_media
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/projections', tags=['projection'])


@router.oauth2_client.get('/', response_model=list[ProjoSelectResult])
async def get_projections(
    status: PROJO_SELECT_STATUS | None = None,
    message_id: int | None = None,
    channel_id: int | None = None,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Get a list of projections."""
    return await projo_select(edgedb, status=status, message_id=message_id, channel_id=channel_id)


@router.oauth2_client_restricted.post(
    '/', response_model=ProjoInsertResult, status_code=status.HTTP_201_CREATED
)
async def new_projection(
    body: NewProjectionBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Create a new projection."""
    return await projo_insert(edgedb, **body.model_dump())


@router.oauth2_client.get(
    '/{id}',
    response_model=ProjoSelectResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_projection(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get a projection by ID."""
    resp = await projo_select(edgedb, id=id)
    if len(resp) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp[0]


@router.oauth2_client_restricted.delete(
    '/{id}', response_model=ProjoDeleteResult, responses={status.HTTP_204_NO_CONTENT: {}}
)
async def delete_projection(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a projection by ID."""
    resp = await projo_delete(edgedb, id=id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client_restricted.put(
    '/{id}/name',
    response_model=ProjoUpdateNameResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def set_projection_name(
    id: UUID, body: SetProjectionNameBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Set the name of a projection."""
    resp = await projo_update_name(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.put(
    '/{id}/status',
    response_model=ProjoUpdateStatusResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def set_projection_status(
    id: UUID, body: SetProjectionStatusBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Set the status of a projection."""
    resp = await projo_update_status(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.put(
    '/{id}/message_id',
    response_model=ProjoUpdateMessageIdResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def set_projection_message_id(
    id: UUID, body: SetProjectionMessageIdBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Set the message ID of a projection."""
    resp = await projo_update_message_id(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.put(
    '/{id}/medias/anilist/{id_al}',
    response_model=ProjoAddMediaResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def add_projection_anilist_media(
    id: UUID, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Add an AniList media to a projection."""
    medias = await fetch_media(id_al)
    if len(medias) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Media Not found')
    # FIXME: merge media in db
    resp = await projo_add_media(edgedb, id=id, id_al=id_al)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Projection Not found')
    return resp


@router.oauth2_client_restricted.post(
    '/{id}/medias/external',
    response_model=ProjoAddExternalMediaResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def add_projection_external_media(
    id: UUID, body: ProjoAddExternalMediaBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Add an external media to a projection."""
    resp = await projo_add_external_media(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.delete(
    '/{id}/medias/anilist/{id_al}',
    response_model=ProjoRemoveMediaResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def remove_projection_media(
    id: UUID, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Remove an AniList media from a projection."""
    resp = await projo_remove_media(edgedb, id=id, id_al=id_al)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client_restricted.delete(
    '/{id}/medias/external/{external_media_id}',
    response_model=ProjoRemoveExternalMediaResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def remove_projection_external_media(
    id: UUID, external_media_id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Remove an external media from a projection."""
    resp = await projo_remove_external_media(edgedb, id=id, external_media_id=external_media_id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client_restricted.put(
    '/{id}/participants/{participant_id}',
    response_model=ProjoParticipantAddResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def add_projection_participant(
    id: UUID,
    participant_id: int,
    body: ParticipantAddBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Add a participant to a projection."""
    resp = await projo_participant_add(
        edgedb,
        id=id,
        participant_id=participant_id,
        **body.model_dump(),
    )
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client_restricted.delete(
    '/{id}/participants/{participant_id}',
    response_model=ProjoParticipantRemoveResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def remove_projection_participant(
    id: UUID,
    participant_id: int,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Remove a participant from a projection."""
    resp = await projo_participant_remove(edgedb, id=id, participant_id=participant_id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client_restricted.put(
    '/{id}/guild_events/{discord_id}',
    response_model=ProjoAddEventResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def add_projection_guild_event(
    id: UUID, discord_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Add a guild event to a projection."""
    resp = await projo_add_event(edgedb, id=id, event_discord_id=discord_id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.delete(
    '/{id}/guild_events/upcoming',
    response_model=ProjoDeleteUpcomingEventsResult,
)
async def delete_upcoming_projection_events(
    id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Delete upcoming guild events from a projection."""
    return await projo_delete_upcoming_events(edgedb, id=id)
