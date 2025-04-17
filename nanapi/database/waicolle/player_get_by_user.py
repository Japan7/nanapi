from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  player := (
    select waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
  ),
select player {
  *,
  user: {
    discord_id,
  },
}
"""


class WaicolleGameMode(StrEnum):
    WAIFU = 'WAIFU'
    HUSBANDO = 'HUSBANDO'
    ALL = 'ALL'


class PlayerGetByUserResultUser(BaseModel):
    discord_id: str


class PlayerGetByUserResult(BaseModel):
    user: PlayerGetByUserResultUser
    id: UUID
    frozen_at: datetime | None
    blood_shards: int
    game_mode: WaicolleGameMode
    moecoins: int


adapter = TypeAdapter(PlayerGetByUserResult | None)


async def player_get_by_user(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
) -> PlayerGetByUserResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
