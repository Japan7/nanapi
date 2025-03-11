from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select waicolle::TradeOperation {
  *,
  author: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  received: {
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
  },
  offeree: {
    user: {
      discord_id,
      discord_id_str,
    },
  },
  offered: {
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
  },
}
filter .client = global client
and not exists .completed_at
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class TradeSelectResultOfferedCustomPositionWaifu(BaseModel):
    id: UUID


class TradeSelectResultOfferedOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeSelectResultOfferedOriginalOwner(BaseModel):
    user: TradeSelectResultOfferedOriginalOwnerUser


class TradeSelectResultOfferedOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeSelectResultOfferedOwner(BaseModel):
    user: TradeSelectResultOfferedOwnerUser


class TradeSelectResultOfferedCharacter(BaseModel):
    id_al: int


class TradeSelectResultOffered(BaseModel):
    character: TradeSelectResultOfferedCharacter
    owner: TradeSelectResultOfferedOwner
    original_owner: TradeSelectResultOfferedOriginalOwner | None
    custom_position_waifu: TradeSelectResultOfferedCustomPositionWaifu | None
    id: UUID
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
    disabled: bool
    frozen: bool


class TradeSelectResultOffereeUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeSelectResultOfferee(BaseModel):
    user: TradeSelectResultOffereeUser


class TradeSelectResultReceivedCustomPositionWaifu(BaseModel):
    id: UUID


class TradeSelectResultReceivedOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeSelectResultReceivedOriginalOwner(BaseModel):
    user: TradeSelectResultReceivedOriginalOwnerUser


class TradeSelectResultReceivedOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeSelectResultReceivedOwner(BaseModel):
    user: TradeSelectResultReceivedOwnerUser


class TradeSelectResultReceivedCharacter(BaseModel):
    id_al: int


class TradeSelectResultReceived(BaseModel):
    character: TradeSelectResultReceivedCharacter
    owner: TradeSelectResultReceivedOwner
    original_owner: TradeSelectResultReceivedOriginalOwner | None
    custom_position_waifu: TradeSelectResultReceivedCustomPositionWaifu | None
    id: UUID
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
    disabled: bool
    frozen: bool


class TradeSelectResultAuthorUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeSelectResultAuthor(BaseModel):
    user: TradeSelectResultAuthorUser


class TradeSelectResult(BaseModel):
    author: TradeSelectResultAuthor
    received: list[TradeSelectResultReceived]
    offeree: TradeSelectResultOfferee
    offered: list[TradeSelectResultOffered]
    id: UUID
    blood_shards: int
    completed_at: datetime | None
    created_at: datetime


adapter = TypeAdapter(list[TradeSelectResult])


async def trade_select(
    executor: AsyncIOExecutor,
) -> list[TradeSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
