from datetime import datetime
from enum import StrEnum
from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  waifus := (
    select waicolle::Waifu
    filter .client = global client
    and .owner = assert_exists(player)
    and .level = 0 and not .blooded
    and not .disabled
  ),
  grouped := (
    group waifus
    using chara_id_al := .character.id_al
    by chara_id_al
  ),
  counted := (
    select grouped {
      count := count(.elements),
    }
  ),
select counted {
  key: { chara_id_al },
  grouping,
  elements: {
    id,
    timestamp,
    level,
    locked,
    trade_locked,
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
  } order by .timestamp desc
}
filter .count >= 3
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuEdgedResultElementsCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuEdgedResultElementsOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuEdgedResultElementsOriginalOwner(BaseModel):
    user: WaifuEdgedResultElementsOriginalOwnerUser


class WaifuEdgedResultElementsOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuEdgedResultElementsOwner(BaseModel):
    user: WaifuEdgedResultElementsOwnerUser


class WaifuEdgedResultElementsCharacter(BaseModel):
    id_al: int


class WaifuEdgedResultElements(BaseModel):
    id: UUID
    timestamp: datetime
    level: int
    locked: bool
    trade_locked: bool
    blooded: bool
    nanaed: bool
    custom_image: str | None
    custom_name: str | None
    custom_collage: bool
    custom_position: WaicolleCollagePosition
    character: WaifuEdgedResultElementsCharacter
    owner: WaifuEdgedResultElementsOwner
    original_owner: WaifuEdgedResultElementsOriginalOwner | None
    custom_position_waifu: WaifuEdgedResultElementsCustomPositionWaifu | None


class WaifuEdgedResultKey(BaseModel):
    chara_id_al: int


class WaifuEdgedResult(BaseModel):
    key: WaifuEdgedResultKey
    grouping: list[str]
    elements: list[WaifuEdgedResultElements]


adapter = TypeAdapter(list[WaifuEdgedResult])


async def waifu_edged(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
) -> list[WaifuEdgedResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
