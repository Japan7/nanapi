from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select waicolle::Player {
  *,
  user: {
    discord_id,
    discord_id_str,
  },
}
filter .client = global client
"""


class WaicolleGameMode(StrEnum):
    WAIFU = 'WAIFU'
    HUSBANDO = 'HUSBANDO'
    ALL = 'ALL'


class PlayerSelectAllResultUser(BaseModel):
    discord_id: int
    discord_id_str: str


class PlayerSelectAllResult(BaseModel):
    user: PlayerSelectAllResultUser
    id: UUID
    frozen_at: datetime | None
    blood_shards: int
    game_mode: WaicolleGameMode
    moecoins: int


adapter = TypeAdapter(list[PlayerSelectAllResult])


async def player_select_all(
    executor: AsyncIOExecutor,
) -> list[PlayerSelectAllResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
