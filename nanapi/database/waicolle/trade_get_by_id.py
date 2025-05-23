# Generated by gel-pydantic-codegen
# pyright: strict
from datetime import datetime
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
select waicolle::TradeOperation {
  *,
  author: {
    user: {
      discord_id,
    },
  },
  received,
  offeree: {
    user: {
      discord_id,
    },
  },
  offered,
}
filter .id = id
"""


class TradeGetByIdResultOffered(BaseModel):
    id: UUID


class TradeGetByIdResultOffereeUser(BaseModel):
    discord_id: str


class TradeGetByIdResultOfferee(BaseModel):
    user: TradeGetByIdResultOffereeUser


class TradeGetByIdResultReceived(BaseModel):
    id: UUID


class TradeGetByIdResultAuthorUser(BaseModel):
    discord_id: str


class TradeGetByIdResultAuthor(BaseModel):
    user: TradeGetByIdResultAuthorUser


class TradeGetByIdResult(BaseModel):
    author: TradeGetByIdResultAuthor
    received: list[TradeGetByIdResultReceived]
    offeree: TradeGetByIdResultOfferee
    offered: list[TradeGetByIdResultOffered]
    id: UUID
    created_at: datetime
    completed_at: datetime | None
    blood_shards: int


adapter = TypeAdapter[TradeGetByIdResult | None](TradeGetByIdResult | None)


async def trade_get_by_id(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
) -> TradeGetByIdResult | None:
    resp = await executor.query_single_json(  # pyright: ignore[reportUnknownMemberType]
        EDGEQL_QUERY,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
