from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  profiles := (
    select user::Profile
    filter .user.discord_id = discord_id
  )
select profiles {
  full_name,
  photo,
  promotion,
  telephone,
  user: {
    discord_id,
    discord_id_str,
  },
}
"""


class ProfileGetByDiscordIdResultUser(BaseModel):
    discord_id: int
    discord_id_str: str


class ProfileGetByDiscordIdResult(BaseModel):
    full_name: str | None
    photo: str | None
    promotion: str | None
    telephone: str | None
    user: ProfileGetByDiscordIdResultUser


adapter = TypeAdapter(ProfileGetByDiscordIdResult | None)


async def profile_get_by_discord_id(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
) -> ProfileGetByDiscordIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
