from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  charas_ids := <array<int32>>$charas_ids,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
for id_al in array_unpack(charas_ids) union (
  with
    chara := (select anilist::Character filter .id_al = id_al),
    inserted := (
      insert waicolle::Waifu {
        client := global client,
        character := chara,
        owner := player,
        original_owner := player,
      }
    ),
  select inserted {
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
)
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class WaifuInsertResultCustomPositionWaifu(BaseModel):
    id: UUID


class WaifuInsertResultOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuInsertResultOriginalOwner(BaseModel):
    user: WaifuInsertResultOriginalOwnerUser


class WaifuInsertResultOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class WaifuInsertResultOwner(BaseModel):
    user: WaifuInsertResultOwnerUser


class WaifuInsertResultCharacter(BaseModel):
    id_al: int


class WaifuInsertResult(BaseModel):
    character: WaifuInsertResultCharacter
    owner: WaifuInsertResultOwner
    original_owner: WaifuInsertResultOriginalOwner | None
    custom_position_waifu: WaifuInsertResultCustomPositionWaifu | None
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


adapter = TypeAdapter(list[WaifuInsertResult])


async def waifu_insert(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    charas_ids: list[int],
) -> list[WaifuInsertResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        charas_ids=charas_ids,
    )
    return adapter.validate_json(resp, strict=False)
