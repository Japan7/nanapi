from datetime import datetime
from enum import StrEnum
from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  hide_singles := <bool>$hide_singles,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  player := assert_exists(player),
  unlocked := (
    select waicolle::Waifu
    filter .client = global client
    and not .locked
    and not .blooded
    and not .disabled
  ),
  tracked := (
    select unlocked
    filter .character.id_al in player.tracked_characters.id_al
    and ((
      with
        chara_id_al := .character.id_al,
        owned := (
          select detached waicolle::Waifu
          filter .character.id_al = chara_id_al
          and .owner = player
          and .locked
        ),
      select count(owned) != 1
    ) if hide_singles else true)
  ),
  duplicated := (
    select unlocked
    filter (
      with
        chara_id_al := .character.id_al,
        owned := (
          select detached waicolle::Waifu
          filter .character.id_al = chara_id_al
          and .owner = player
          and .locked
        ),
      select count(owned) > 1
    )
  ),
select distinct (tracked union duplicated) {
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
order by .timestamp desc
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuTrackUnlockedResultCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuTrackUnlockedResultOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuTrackUnlockedResultOriginalOwner(BaseModel):
    user: WaifuTrackUnlockedResultOriginalOwnerUser


class WaifuTrackUnlockedResultOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuTrackUnlockedResultOwner(BaseModel):
    user: WaifuTrackUnlockedResultOwnerUser


class WaifuTrackUnlockedResultCharacter(BaseModel):
    id_al: int


class WaifuTrackUnlockedResult(BaseModel):
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
    character: WaifuTrackUnlockedResultCharacter
    owner: WaifuTrackUnlockedResultOwner
    original_owner: WaifuTrackUnlockedResultOriginalOwner | None
    custom_position_waifu: WaifuTrackUnlockedResultCustomPositionWaifu | None


adapter = TypeAdapter(list[WaifuTrackUnlockedResult])


async def waifu_track_unlocked(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    hide_singles: bool,
) -> list[WaifuTrackUnlockedResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        hide_singles=hide_singles,
    )
    return adapter.validate_json(resp, strict=False)
