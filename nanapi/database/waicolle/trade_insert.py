from datetime import datetime
from enum import StrEnum
from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  author_discord_id := <int64>$author_discord_id,
  received_ids := <array<uuid>>$received_ids,
  blood_shards := <optional int32>$blood_shards ?? 0,
  offeree_discord_id := <int64>$offeree_discord_id,
  offered_ids := <array<uuid>>$offered_ids,
  author := (select waicolle::Player filter .client = global client and .user.discord_id = author_discord_id),
  offeree := (select waicolle::Player filter .client = global client and .user.discord_id = offeree_discord_id),
  inserted := (
    insert waicolle::TradeOperation {
      client := global client,
      author := author,
      received := (select waicolle::Waifu filter .id in array_unpack(received_ids)),
      blood_shards := blood_shards,
      offeree := offeree,
      offered := (select waicolle::Waifu filter .id in array_unpack(offered_ids)),
    }
  )
select inserted {
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
"""


class WaicolleCollagePosition(StrEnum):
    DEFAULT = 'DEFAULT'
    LEFT_OF = 'LEFT_OF'
    RIGHT_OF = 'RIGHT_OF'


class TradeInsertResultOfferedCustomPositionWaifu(BaseModel):
    id: UUID


class TradeInsertResultOfferedOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeInsertResultOfferedOriginalOwner(BaseModel):
    user: TradeInsertResultOfferedOriginalOwnerUser


class TradeInsertResultOfferedOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeInsertResultOfferedOwner(BaseModel):
    user: TradeInsertResultOfferedOwnerUser


class TradeInsertResultOfferedCharacter(BaseModel):
    id_al: int


class TradeInsertResultOffered(BaseModel):
    character: TradeInsertResultOfferedCharacter
    owner: TradeInsertResultOfferedOwner
    original_owner: TradeInsertResultOfferedOriginalOwner | None
    custom_position_waifu: TradeInsertResultOfferedCustomPositionWaifu | None
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


class TradeInsertResultOffereeUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeInsertResultOfferee(BaseModel):
    user: TradeInsertResultOffereeUser


class TradeInsertResultReceivedCustomPositionWaifu(BaseModel):
    id: UUID


class TradeInsertResultReceivedOriginalOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeInsertResultReceivedOriginalOwner(BaseModel):
    user: TradeInsertResultReceivedOriginalOwnerUser


class TradeInsertResultReceivedOwnerUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeInsertResultReceivedOwner(BaseModel):
    user: TradeInsertResultReceivedOwnerUser


class TradeInsertResultReceivedCharacter(BaseModel):
    id_al: int


class TradeInsertResultReceived(BaseModel):
    character: TradeInsertResultReceivedCharacter
    owner: TradeInsertResultReceivedOwner
    original_owner: TradeInsertResultReceivedOriginalOwner | None
    custom_position_waifu: TradeInsertResultReceivedCustomPositionWaifu | None
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


class TradeInsertResultAuthorUser(BaseModel):
    discord_id: int
    discord_id_str: str


class TradeInsertResultAuthor(BaseModel):
    user: TradeInsertResultAuthorUser


class TradeInsertResult(BaseModel):
    author: TradeInsertResultAuthor
    received: list[TradeInsertResultReceived]
    offeree: TradeInsertResultOfferee
    offered: list[TradeInsertResultOffered]
    created_at: datetime
    completed_at: datetime | None
    blood_shards: int
    id: UUID


adapter = TypeAdapter(TradeInsertResult)


async def trade_insert(
    executor: AsyncIOExecutor,
    *,
    author_discord_id: int,
    received_ids: list[UUID],
    offeree_discord_id: int,
    offered_ids: list[UUID],
    blood_shards: int | None = None,
) -> TradeInsertResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        author_discord_id=author_discord_id,
        received_ids=received_ids,
        offeree_discord_id=offeree_discord_id,
        offered_ids=offered_ids,
        blood_shards=blood_shards,
    )
    return adapter.validate_json(resp, strict=False)
