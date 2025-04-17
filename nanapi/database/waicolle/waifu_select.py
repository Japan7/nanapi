from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  ids := <array<uuid>>$ids,
select waicolle::Waifu {
  *,
  character: { id_al },
  owner: {
    user: {
      discord_id,
    },
  },
  original_owner: {
    user: {
      discord_id,
    },
  },
  custom_position_waifu: { id },
}
filter .id in array_unpack(ids)
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuSelectResultCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuSelectResultOriginalOwnerUser(BaseModel):
    discord_id: str


class WaifuSelectResultOriginalOwner(BaseModel):
    user: WaifuSelectResultOriginalOwnerUser


class WaifuSelectResultOwnerUser(BaseModel):
    discord_id: str


class WaifuSelectResultOwner(BaseModel):
    user: WaifuSelectResultOwnerUser


class WaifuSelectResultCharacter(BaseModel):
    id_al: int


class WaifuSelectResult(BaseModel):
    character: WaifuSelectResultCharacter
    owner: WaifuSelectResultOwner
    original_owner: WaifuSelectResultOriginalOwner | None
    custom_position_waifu: WaifuSelectResultCustomPositionWaifu | None
    id: UUID
    frozen: bool
    disabled: bool
    blooded: bool
    custom_collage: bool
    custom_image: str | None
    custom_name: str | None
    custom_position: WaicolleCollagePosition
    level: int
    locked: bool
    nanaed: bool
    timestamp: datetime
    trade_locked: bool


adapter = TypeAdapter(list[WaifuSelectResult])


async def waifu_select(
    executor: AsyncIOExecutor,
    *,
    ids: list[UUID],
) -> list[WaifuSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        ids=ids,
    )
    return adapter.validate_json(resp, strict=False)
