from datetime import datetime

from fastapi import Depends, HTTPException, Response, status
from gel import AsyncIOClient

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
from nanapi.database.calendar.guild_event_select import GuildEventSelectResult, guild_event_select
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
    """Get all user calendars."""
    return await user_calendar_select_all(get_edgedb())


@router.oauth2.get(
    '/user_calendars/{discord_id}',
    response_model=UserCalendarSelectResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_user_calendar(discord_id: str):
    """Get a user calendar by Discord ID."""
    resp = await user_calendar_select(get_edgedb(), discord_id=discord_id)
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2.patch('/user_calendars/{discord_id}', response_model=UserCalendarMergeResult)
async def upsert_user_calendar(discord_id: str, body: UpsertUserCalendarBody):
    """Upsert (update or insert) a user calendar."""
    return await user_calendar_merge(get_edgedb(), discord_id=discord_id, **body.model_dump())


@router.oauth2.delete(
    '/user_calendars/{discord_id}',
    response_model=UserCalendarDeleteResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def delete_user_calendar(discord_id: str):
    """Delete a user calendar by Discord ID."""
    resp = await user_calendar_delete(get_edgedb(), discord_id=discord_id)
    if resp is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client.get(
    '/guild_events',
    response_model=list[GuildEventSelectResult],
)
async def get_guild_events(
    start_after: datetime | None = None,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Get all guild events, optionally after a certain date."""
    return await guild_event_select(edgedb, start_after=start_after)


@router.oauth2_client_restricted.put(
    '/guild_events/{discord_id}',
    response_model=GuildEventMergeResult,
)
async def upsert_guild_event(
    discord_id: str,
    body: UpsertGuildEventBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Upsert (update or insert) a guild event."""
    return await guild_event_merge(edgedb, discord_id=discord_id, **body.model_dump())


@router.oauth2_client_restricted.delete(
    '/guild_events/{discord_id}',
    response_model=GuildEventDeleteResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def delete_guild_event(discord_id: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a guild event by Discord ID."""
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
    discord_id: str,
    participant_id: str,
    body: ParticipantAddBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Add a participant to a guild event."""
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
    discord_id: str,
    participant_id: str,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Remove a participant from a guild event."""
    resp = await guild_event_participant_remove(
        edgedb,
        discord_id=discord_id,
        participant_id=participant_id,
    )
    if resp is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.public.get('/ics', responses={status.HTTP_404_NOT_FOUND: {}})
async def get_ics(client: str, user: str | None = None, aggregate: bool = False):
    """Get an iCalendar (ICS) file for a client and optionally a user."""
    _client = await client_get_by_username(get_edgedb(), username=client)
    if _client is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    edgedb = get_client_edgedb(_client.id)

    events = await guild_event_select(edgedb, discord_id=user)

    user_calendar = None
    if user is not None and aggregate:
        user_calendar = await user_calendar_select(get_edgedb(), discord_id=user)

    calendar = await ics_from_events(events, user_calendar)

    return Response(content=calendar.to_ical(), media_type='text/calendar')
