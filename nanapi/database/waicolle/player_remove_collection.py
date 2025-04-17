from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  id := <uuid>$id,
  collection := (select waicolle::Collection filter .id = id),
update waicolle::Player
filter .client = global client and .user.discord_id = discord_id
set {
  tracked_collections -= collection,
}
"""


class PlayerRemoveCollectionResult(BaseModel):
    id: UUID


adapter = TypeAdapter(PlayerRemoveCollectionResult | None)


async def player_remove_collection(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    id: UUID,
) -> PlayerRemoveCollectionResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
