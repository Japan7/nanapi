from datetime import datetime

from edgedb import AsyncIOClient
from fastapi import Depends, HTTPException, Response, status

from nanapi.database.calendar.guild_event_delete import GuildEventDeleteResult, guild_event_delete
from nanapi.database.calendar.guild_event_merge import GuildEventMergeResult, guild_event_merge
from nanapi.database.calendar.guild_event_participant_add import (
    GuildEventParticipantAddResult,
    guild_event_participant_add,
)
from nanapi.database.calendar.guild_event_participant_remove import (
    GuildEventParticipantRemoveResult,
    guild_event_participant_remove,
)
from nanapi.database.calendar.guild_event_select_all import (
    GuildEventSelectAllResult,
    guild_event_select_all,
)
from nanapi.database.calendar.guild_event_select_participant import guild_event_select_participant
from nanapi.database.calendar.user_calendar_delete import (
    UserCalendarDeleteResult,
    user_calendar_delete,
)
from nanapi.database.calendar.user_calendar_merge import (
    UserCalendarMergeResult,
    user_calendar_merge,
)
from nanapi.database.calendar.user_calendar_select import (
    UserCalendarSelectResult,
    user_calendar_select,
)
from nanapi.database.calendar.user_calendar_select_all import (
    UserCalendarSelectAllResult,
    user_calendar_select_all,
)
from nanapi.database.default.client_get_by_username import client_get_by_username
from nanapi.models.calendar import UpsertGuildEventBody, UpsertUserCalendarBody
from nanapi.models.common import ParticipantAddBody
from nanapi.utils.calendar import ics_from_events
from nanapi.utils.clients import get_edgedb
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/calendar', tags=['calendar'])


@router.oauth2.get('/user_calendars', response_model=list[UserCalendarSelectAllResult])
async def get_user_calendars():
    return await user_calendar_select_all(get_edgedb())


@router.oauth2.get(
    '/user_calendars/{discord_id}',
    response_model=UserCalendarSelectResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_user_calendar(discord_id: int):
    resp = await user_calendar_select(get_edgedb(), discord_id=discord_id)
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2.patch('/user_calendars/{discord_id}', response_model=UserCalendarMergeResult)
async def upsert_user_calendar(discord_id: int, body: UpsertUserCalendarBody):
    return await user_calendar_merge(get_edgedb(), discord_id=discord_id, **body.model_dump())


@router.oauth2.delete(
    '/user_calendars/{discord_id}',
    response_model=UserCalendarDeleteResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def delete_user_calendar(discord_id: int):
    resp = await user_calendar_delete(get_edgedb(), discord_id=discord_id)
    if resp is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client.get(
    '/guild_events',
    response_model=list[GuildEventSelectAllResult],
)
async def get_guild_events(
    start_after: datetime | None = None,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    return await guild_event_select_all(edgedb, start_after=start_after)


@router.oauth2_client_restricted.put(
    '/guild_events/{discord_id}',
    response_model=GuildEventMergeResult,
)
async def upsert_guild_event(
    discord_id: int,
    body: UpsertGuildEventBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    return await guild_event_merge(edgedb, discord_id=discord_id, **body.model_dump())


@router.oauth2_client_restricted.delete(
    '/guild_events/{discord_id}',
    response_model=GuildEventDeleteResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def delete_guild_event(discord_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    resp = await guild_event_delete(edgedb, discord_id=discord_id)
    if resp is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.put(
    '/guild_events/{discord_id}/participants/{participant_id}',
    response_model=GuildEventParticipantAddResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def add_guild_event_participant(
    discord_id: int,
    participant_id: int,
    body: ParticipantAddBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    resp = await guild_event_participant_add(
        edgedb,
        discord_id=discord_id,
        participant_id=participant_id,
        **body.model_dump(),
    )
    if resp is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.delete(
    '/guild_events/{discord_id}/participants/{participant_id}',
    response_model=GuildEventParticipantRemoveResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def remove_guild_event_participant(
    discord_id: int,
    participant_id: int,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    resp = await guild_event_participant_remove(
        edgedb,
        discord_id=discord_id,
        participant_id=participant_id,
    )
    if resp is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.basic_auth.get('/ics', responses={status.HTTP_404_NOT_FOUND: {}})
async def get_ics(client: str, discord_id: int):
    _client = await client_get_by_username(get_edgedb(), username=client)
    if _client is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    edgedb = get_client_edgedb(_client.id)
    events = await guild_event_select_participant(edgedb, discord_id=discord_id)
    calendar = ics_from_events(events)
    return Response(content=calendar.serialize(), media_type='text/calendar')
