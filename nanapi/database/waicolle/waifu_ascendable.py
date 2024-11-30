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
    and not .trade_locked and not .blooded
    and not .disabled
  ),
  grouped := (
    group waifus
    using chara_id_al := .character.id_al
    by chara_id_al, .level
  ),
  counted := (
    select grouped {
      count := count(.elements),
    }
  ),
select counted {
  key: { chara_id_al, level },
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
filter .count >= 4
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuAscendableResultElementsCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuAscendableResultElementsOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuAscendableResultElementsOriginalOwner(BaseModel):
    user: WaifuAscendableResultElementsOriginalOwnerUser


class WaifuAscendableResultElementsOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuAscendableResultElementsOwner(BaseModel):
    user: WaifuAscendableResultElementsOwnerUser


class WaifuAscendableResultElementsCharacter(BaseModel):
    id_al: int


class WaifuAscendableResultElements(BaseModel):
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
    character: WaifuAscendableResultElementsCharacter
    owner: WaifuAscendableResultElementsOwner
    original_owner: WaifuAscendableResultElementsOriginalOwner | None
    custom_position_waifu: WaifuAscendableResultElementsCustomPositionWaifu | None


class WaifuAscendableResultKey(BaseModel):
    chara_id_al: int
    level: int


class WaifuAscendableResult(BaseModel):
    key: WaifuAscendableResultKey
    grouping: list[str]
    elements: list[WaifuAscendableResultElements]


adapter = TypeAdapter(list[WaifuAscendableResult])


async def waifu_ascendable(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
) -> list[WaifuAscendableResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
