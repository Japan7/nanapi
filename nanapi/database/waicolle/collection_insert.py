from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  name := <str>$name,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  inserted := (
    insert waicolle::Collection {
      client := global client,
      name := name,
      author := player,
    }
  ),
select inserted {
  id,
  name,
  author: {
    user: {
      discord_id,
    },
  },
}
"""


class CollectionInsertResultAuthorUser(BaseModel):
    discord_id: str


class CollectionInsertResultAuthor(BaseModel):
    user: CollectionInsertResultAuthorUser


class CollectionInsertResult(BaseModel):
    id: UUID
    name: str
    author: CollectionInsertResultAuthor


adapter = TypeAdapter(CollectionInsertResult)


async def collection_insert(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    name: str,
) -> CollectionInsertResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        name=name,
    )
    return adapter.validate_json(resp, strict=False)
