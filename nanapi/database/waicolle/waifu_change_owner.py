# Generated by gel-pydantic-codegen
# pyright: strict
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  ids := <array<uuid>>$ids,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  updated := (
    update waicolle::Waifu
    filter .id in array_unpack(ids)
    set {
      timestamp := datetime_current(),
      locked := false,
      custom_collage := false,
      custom_position := waicolle::CollagePosition.DEFAULT,
      owner := player,
      custom_position_waifu := {},
    }
  )
select updated {
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
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuChangeOwnerResultCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuChangeOwnerResultOriginalOwnerUser(BaseModel):
    discord_id: str


class WaifuChangeOwnerResultOriginalOwner(BaseModel):
    user: WaifuChangeOwnerResultOriginalOwnerUser


class WaifuChangeOwnerResultOwnerUser(BaseModel):
    discord_id: str


class WaifuChangeOwnerResultOwner(BaseModel):
    user: WaifuChangeOwnerResultOwnerUser


class WaifuChangeOwnerResultCharacter(BaseModel):
    id_al: int


class WaifuChangeOwnerResult(BaseModel):
    character: WaifuChangeOwnerResultCharacter
    owner: WaifuChangeOwnerResultOwner
    original_owner: WaifuChangeOwnerResultOriginalOwner | None
    custom_position_waifu: WaifuChangeOwnerResultCustomPositionWaifu | None
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
    disabled: bool
    frozen: bool
    id: UUID


adapter = TypeAdapter[list[WaifuChangeOwnerResult]](list[WaifuChangeOwnerResult])


async def waifu_change_owner(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    ids: list[UUID],
) -> list[WaifuChangeOwnerResult]:
    resp = await executor.query_json(  # pyright: ignore[reportUnknownMemberType]
        EDGEQL_QUERY,
        discord_id=discord_id,
        ids=ids,
    )
    return adapter.validate_json(resp, strict=False)
