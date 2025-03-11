from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id_al := <int32>$id_al,
  character := (select anilist::Character filter .id_al = id_al),
select waicolle::Player {
  *,
  user: {
    discord_id,
    discord_id_str,
  },
}
filter .client = global client
and character in .tracked_characters
"""


class WaicolleGameMode(StrEnum):
    WAIFU = 'WAIFU'
    HUSBANDO = 'HUSBANDO'
    ALL = 'ALL'


class PlayerSelectByCharaResultUser(BaseModel):
    discord_id: int
    discord_id_str: str


class PlayerSelectByCharaResult(BaseModel):
    user: PlayerSelectByCharaResultUser
    id: UUID
    blood_shards: int
    game_mode: WaicolleGameMode
    moecoins: int
    frozen_at: datetime | None


adapter = TypeAdapter(list[PlayerSelectByCharaResult])


async def player_select_by_chara(
    executor: AsyncIOExecutor,
    *,
    id_al: int,
) -> list[PlayerSelectByCharaResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
