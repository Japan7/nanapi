from datetime import datetime
from enum import StrEnum
from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id_al := <int32>$id_al,
select waicolle::Waifu {
  id,
  timestamp,
  trade_locked,
  level,
  locked,
  blooded,
  nanaed,
  custom_image,
  custom_name,
  custom_collage,
  custom_position,
  character: { id_al },
  owner: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  original_owner: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  custom_position_waifu: { id },
}
filter .client = global client
and .character.id_al = id_al
and not .disabled
order by .timestamp desc
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuSelectByCharaResultCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuSelectByCharaResultOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuSelectByCharaResultOriginalOwner(BaseModel):
    user: WaifuSelectByCharaResultOriginalOwnerUser


class WaifuSelectByCharaResultOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuSelectByCharaResultOwner(BaseModel):
    user: WaifuSelectByCharaResultOwnerUser


class WaifuSelectByCharaResultCharacter(BaseModel):
    id_al: int


class WaifuSelectByCharaResult(BaseModel):
    id: UUID
    timestamp: datetime
    trade_locked: bool
    level: int
    locked: bool
    blooded: bool
    nanaed: bool
    custom_image: str | None
    custom_name: str | None
    custom_collage: bool
    custom_position: WaicolleCollagePosition
    character: WaifuSelectByCharaResultCharacter
    owner: WaifuSelectByCharaResultOwner
    original_owner: WaifuSelectByCharaResultOriginalOwner | None
    custom_position_waifu: WaifuSelectByCharaResultCustomPositionWaifu | None


adapter = TypeAdapter(list[WaifuSelectByCharaResult])


async def waifu_select_by_chara(
    executor: AsyncIOExecutor,
    *,
    id_al: int,
) -> list[WaifuSelectByCharaResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
