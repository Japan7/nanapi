# Generated by gel-pydantic-codegen
# pyright: strict
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  author_discord_id := <str>$author_discord_id,
  received_ids := <array<uuid>>$received_ids,
  rerolled_ids := <array<uuid>>$rerolled_ids,
  author := (select waicolle::Player filter .client = global client and .user.discord_id = author_discord_id),
insert waicolle::RerollOperation {
  client := global client,
  author := author,
  received := (select waicolle::Waifu filter .id in array_unpack(received_ids)),
  rerolled := (select waicolle::Waifu filter .id in array_unpack(rerolled_ids)),
}
"""


class RerollopInsertResult(BaseModel):
    id: UUID


adapter = TypeAdapter[RerollopInsertResult](RerollopInsertResult)


async def rerollop_insert(
    executor: AsyncIOExecutor,
    *,
    author_discord_id: str,
    received_ids: list[UUID],
    rerolled_ids: list[UUID],
) -> RerollopInsertResult:
    resp = await executor.query_single_json(  # pyright: ignore[reportUnknownMemberType]
        EDGEQL_QUERY,
        author_discord_id=author_discord_id,
        received_ids=received_ids,
        rerolled_ids=rerolled_ids,
    )
    return adapter.validate_json(resp, strict=False)
