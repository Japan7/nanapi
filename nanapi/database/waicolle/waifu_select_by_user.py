from datetime import datetime
from enum import StrEnum
from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  characters_ids_al := <optional array<int32>>$characters_ids_al,
  level := <optional int32>$level,
  locked := <optional bool>$locked,
  trade_locked := <optional bool>$trade_locked,
  blooded := <optional bool>$blooded,
  nanaed := <optional bool>$nanaed,
  custom_collage := <optional bool>$custom_collage,
  ascended := <optional bool>$ascended,
  disabled := <optional bool>$disabled,
  as_og := <optional bool>$as_og ?? false,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
select waicolle::Waifu {
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
}
filter .client = global client
and (.owner = assert_exists(player) if not as_og else .original_owner = assert_exists(player))
and (.character.id_al in array_unpack(characters_ids_al) if exists characters_ids_al else true)
and (.level = level if exists level else true)
and (.locked = locked if exists locked else true)
and (.trade_locked = trade_locked if exists trade_locked else true)
and (.blooded = blooded if exists blooded else true)
and (.nanaed = nanaed if exists nanaed else true)
and (.custom_collage = custom_collage if exists custom_collage else true)
and (.level > 0 if exists ascended else true)
and (.disabled = disabled if exists disabled else false)
order by .timestamp desc
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuSelectByUserResultCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuSelectByUserResultOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuSelectByUserResultOriginalOwner(BaseModel):
    user: WaifuSelectByUserResultOriginalOwnerUser


class WaifuSelectByUserResultOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuSelectByUserResultOwner(BaseModel):
    user: WaifuSelectByUserResultOwnerUser


class WaifuSelectByUserResultCharacter(BaseModel):
    id_al: int


class WaifuSelectByUserResult(BaseModel):
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
    character: WaifuSelectByUserResultCharacter
    owner: WaifuSelectByUserResultOwner
    original_owner: WaifuSelectByUserResultOriginalOwner | None
    custom_position_waifu: WaifuSelectByUserResultCustomPositionWaifu | None


adapter = TypeAdapter(list[WaifuSelectByUserResult])


async def waifu_select_by_user(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    characters_ids_al: list[int] | None = None,
    level: int | None = None,
    locked: bool | None = None,
    trade_locked: bool | None = None,
    blooded: bool | None = None,
    nanaed: bool | None = None,
    custom_collage: bool | None = None,
    ascended: bool | None = None,
    disabled: bool | None = None,
    as_og: bool | None = None,
) -> list[WaifuSelectByUserResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        characters_ids_al=characters_ids_al,
        level=level,
        locked=locked,
        trade_locked=trade_locked,
        blooded=blooded,
        nanaed=nanaed,
        custom_collage=custom_collage,
        ascended=ascended,
        disabled=disabled,
        as_og=as_og,
    )
    return adapter.validate_json(resp, strict=False)
