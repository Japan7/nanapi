from datetime import datetime

from pydantic import BaseModel


class UpsertUserCalendarBody(BaseModel):
    discord_username: str
    ics: str


class UpsertGuildEventBody(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    start_time: datetime
    end_time: datetime
    image: str | None = None
    url: str | None = None
    organizer_id: str
    organizer_username: str
