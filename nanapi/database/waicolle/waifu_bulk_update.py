from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  ids := <array<uuid>>$ids,
  locked := <optional bool>$locked,
  blooded := <optional bool>$blooded,
  nanaed := <optional bool>$nanaed,
  level := <optional int32>$level,
  custom_collage := <optional bool>$custom_collage,
  timestamp := <optional datetime>$timestamp,
  updated := (
    update waicolle::Waifu
    filter .id in array_unpack(ids)
    set {
      locked := locked ?? .locked,
      blooded := blooded ?? .blooded,
      nanaed := nanaed ?? .nanaed,
      level := level ?? .level,
      custom_collage := custom_collage ?? .custom_collage,
      timestamp := timestamp ?? .timestamp,
    }
  )
select updated {
  *,
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
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuBulkUpdateResultCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuBulkUpdateResultOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuBulkUpdateResultOriginalOwner(BaseModel):
    user: WaifuBulkUpdateResultOriginalOwnerUser


class WaifuBulkUpdateResultOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuBulkUpdateResultOwner(BaseModel):
    user: WaifuBulkUpdateResultOwnerUser


class WaifuBulkUpdateResultCharacter(BaseModel):
    id_al: int


class WaifuBulkUpdateResult(BaseModel):
    character: WaifuBulkUpdateResultCharacter
    owner: WaifuBulkUpdateResultOwner
    original_owner: WaifuBulkUpdateResultOriginalOwner | None
    custom_position_waifu: WaifuBulkUpdateResultCustomPositionWaifu | None
    frozen: bool
    disabled: bool
    trade_locked: bool
    timestamp: datetime
    nanaed: bool
    locked: bool
    level: int
    custom_position: WaicolleCollagePosition
    custom_name: str | None
    custom_image: str | None
    custom_collage: bool
    blooded: bool
    id: UUID


adapter = TypeAdapter(list[WaifuBulkUpdateResult])


async def waifu_bulk_update(
    executor: AsyncIOExecutor,
    *,
    ids: list[UUID],
    locked: bool | None = None,
    blooded: bool | None = None,
    nanaed: bool | None = None,
    level: int | None = None,
    custom_collage: bool | None = None,
    timestamp: datetime | None = None,
) -> list[WaifuBulkUpdateResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        ids=ids,
        locked=locked,
        blooded=blooded,
        nanaed=nanaed,
        level=level,
        custom_collage=custom_collage,
        timestamp=timestamp,
    )
    return adapter.validate_json(resp, strict=False)
