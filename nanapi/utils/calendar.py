from typing import cast

from icalendar import Calendar, Event, vCalAddress

from nanapi.database.calendar.guild_event_select import GuildEventSelectResult
from nanapi.database.calendar.user_calendar_select import UserCalendarSelectResult
from nanapi.utils.clients import get_session


async def ics_from_events(
    events: list[GuildEventSelectResult],
    user_calendar: UserCalendarSelectResult | None = None,
) -> Calendar:
    calendar = Calendar.new()
    for event in events:
        calendar.add_component(to_ics_event(event))
    if user_calendar:
        ics_url = user_calendar.ics.replace('webcal://', 'https://')
        async with get_session().get(ics_url) as resp:
            resp.raise_for_status()
            ics_str = await resp.text()
        user_cal = cast(Calendar, Calendar.from_ical(ics_str))  # pyright: ignore[reportUnknownMemberType]
        calendar.events.extend(user_cal.events)
    return calendar


def to_ics_event(event: GuildEventSelectResult) -> Event:
    return Event.new(
        summary=event.name,
        description=event.description,
        start=event.start_time,
        end=event.end_time,
        location=event.location,
        url=event.url,
        organizer=vCalAddress.new(
            event.organizer.discord_username,
            cn=event.organizer.discord_username,
        ),
        attendees=[
            vCalAddress.new(
                participant.discord_username,
                cn=participant.discord_username,
            )
            for participant in event.participants
        ],
    )
