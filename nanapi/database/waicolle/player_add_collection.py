from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  id := <uuid>$id,
  collection := (select waicolle::Collection filter .id = id),
  _update := (
    update waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
    set {
      tracked_collections += collection,
    }
  )
select {
  player := assert_exists(_update),
  collection := assert_exists(collection) {
    id,
    name,
  },
}
"""


class PlayerAddCollectionResultCollection(BaseModel):
    id: UUID
    name: str


class PlayerAddCollectionResultPlayer(BaseModel):
    id: UUID


class PlayerAddCollectionResult(BaseModel):
    player: PlayerAddCollectionResultPlayer
    collection: PlayerAddCollectionResultCollection


adapter = TypeAdapter(PlayerAddCollectionResult)


async def player_add_collection(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    id: UUID,
) -> PlayerAddCollectionResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
