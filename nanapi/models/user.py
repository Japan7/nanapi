from datetime import datetime

from pydantic import BaseModel

from nanapi.database.user.profile_get_by_discord_id import ProfileGetByDiscordIdResult


class UpsertDiscordAccountBodyItem(BaseModel):
    discord_id: str
    discord_username: str


class ProfileSearchResult(ProfileGetByDiscordIdResult):
    pass


class UpsertProfileBody(BaseModel):
    birthday: datetime | None = None
    discord_username: str
    full_name: str | None = None
    graduation_year: int | None = None
    n7_major: str | None = None
    photo: str | None = None
    pronouns: str | None = None
    telephone: str | None = None
