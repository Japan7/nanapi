from pydantic import BaseModel

from nanapi.database.user.profile_get_by_discord_id import ProfileGetByDiscordIdResult


class UpsertDiscordAccountBodyItem(BaseModel):
    discord_id: int
    discord_username: str


class ProfileSearchResult(ProfileGetByDiscordIdResult):
    pass


class UpsertProfileBody(BaseModel):
    discord_username: str
    full_name: str | None = None
    photo: str | None = None
    promotion: str | None = None
    telephone: str | None = None
