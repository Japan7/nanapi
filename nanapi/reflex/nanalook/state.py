import asyncio
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, Any

import reflex as rx

from nanapi.database.calendar.guild_event_select import guild_event_select
from nanapi.database.calendar.user_calendar_select import user_calendar_select
from nanapi.database.projection.projo_select import ProjoSelectResult, projo_select
from nanapi.database.user.user_select import UserSelectResult, user_select
from nanapi.reflex.state import BaseState
from nanapi.utils.calendar import ics_from_events

from .utils.calendar import calendar_to_events, string_to_hsl


@dataclass
class ParticipantLegend:
    username: str
    color: str


class NanalookState(BaseState):
    projections: list[ProjoSelectResult] = []
    calendar_events: list[dict[str, Any]] = []

    @rx.event
    async def load_projections(self):
        if self.projections:
            return
        assert self._client_executor
        resp = await projo_select(self._client_executor, status='ONGOING')
        self.projections = list(reversed(resp))

    async def _user_events(self, discord_id: str, discord_username: str) -> list[dict[str, Any]]:
        assert self._client_executor
        events, user_calendar = await asyncio.gather(
            guild_event_select(self._client_executor, discord_id=discord_id),
            user_calendar_select(self._client_executor, discord_id=discord_id),
        )
        calendar = await ics_from_events(events, user_calendar)
        return calendar_to_events(calendar, discord_username, string_to_hsl(discord_id))


class ProjectionNanalookState(NanalookState):
    if TYPE_CHECKING:
        projection_id: str

    @rx.var
    def selected(self) -> ProjoSelectResult | None:
        for projo in self.projections:
            if str(projo.id) == self.projection_id:
                return projo
        return None

    @rx.var
    def participant_legends(self) -> list[ParticipantLegend]:
        if not self.selected:
            return []
        legends = [
            ParticipantLegend(
                username=participant.discord_username,
                color=string_to_hsl(str(participant.discord_id)),
            )
            for participant in self.selected.participants
        ]
        return sorted(legends, key=lambda x: x.username.lower())

    @rx.event(background=True)
    async def load_calendar_events(self):
        async with self:
            self.calendar_events = []
            if not self.selected:
                return
            tasks = (
                self._user_events(participant.discord_id, participant.discord_username)
                for participant in self.selected.participants
            )
        events = list(chain.from_iterable(await asyncio.gather(*tasks)))
        async with self:
            self.calendar_events = events


class CustomNanalookState(NanalookState):
    @rx.var
    def _discord_ids(self) -> list[str]:
        users_param = self.router.url.query_parameters.get('users', '')
        return [d.strip() for d in users_param.split(',') if d.strip()]

    @rx.var
    async def _all_users(self) -> dict[str, UserSelectResult]:
        resp = await user_select(self._global_executor)
        return {user.discord_id: user for user in resp}

    @rx.var
    async def participant_legends(self) -> list[ParticipantLegend]:
        all_users = await self._all_users
        legends = [
            ParticipantLegend(
                username=all_users[discord_id].discord_username,
                color=string_to_hsl(discord_id),
            )
            for discord_id in self._discord_ids
        ]
        return sorted(legends, key=lambda x: x.username.lower())

    @rx.event(background=True)
    async def load_calendar_events(self):
        async with self:
            all_users = await self._all_users
            tasks = (
                self._user_events(discord_id, all_users[discord_id].discord_username)
                for discord_id in self._discord_ids
            )
        events = list(chain.from_iterable(await asyncio.gather(*tasks)))
        async with self:
            self.calendar_events = events
