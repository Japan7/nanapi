from datetime import datetime

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  profiles := (
    select user::Profile
    filter .user.discord_id = discord_id
  )
select profiles {
  birthday,
  full_name,
  graduation_year,
  photo,
  pronouns,
  n7_major,
  telephone,
  user: {
    discord_id,
  },
}
"""


class ProfileGetByDiscordIdResultUser(BaseModel):
    discord_id: str


class ProfileGetByDiscordIdResult(BaseModel):
    birthday: datetime | None
    full_name: str | None
    graduation_year: int | None
    photo: str | None
    pronouns: str | None
    n7_major: str | None
    telephone: str | None
    user: ProfileGetByDiscordIdResultUser


adapter = TypeAdapter(ProfileGetByDiscordIdResult | None)


async def profile_get_by_discord_id(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
) -> ProfileGetByDiscordIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
