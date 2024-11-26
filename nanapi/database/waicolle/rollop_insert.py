from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  author_discord_id := <int64>$author_discord_id,
  received_ids := <array<uuid>>$received_ids,
  roll_id := <str>$roll_id,
  moecoins := <optional int32>$moecoins ?? 0,
  author := (select waicolle::Player filter .client = global client and .user.discord_id = author_discord_id),
insert waicolle::RollOperation {
  client := global client,
  author := author,
  received := (select waicolle::Waifu filter .id in array_unpack(received_ids)),
  roll_id := roll_id,
  moecoins := moecoins,
}
"""


class RollopInsertResult(BaseModel):
    id: UUID


adapter = TypeAdapter(RollopInsertResult)


async def rollop_insert(
    executor: AsyncIOExecutor,
    *,
    author_discord_id: int,
    received_ids: list[UUID],
    roll_id: str,
    moecoins: int | None = None,
) -> RollopInsertResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        author_discord_id=author_discord_id,
        received_ids=received_ids,
        roll_id=roll_id,
        moecoins=moecoins,
    )
    return adapter.validate_json(resp, strict=False)
