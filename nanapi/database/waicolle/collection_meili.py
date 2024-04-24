from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
group waicolle::Collection {
  id,
  name,
  author: {
    user: {
      discord_id,
    },
  },
}
by .client
"""


class CollectionMeiliResultElementsAuthorUser(BaseModel):
    discord_id: int


class CollectionMeiliResultElementsAuthor(BaseModel):
    user: CollectionMeiliResultElementsAuthorUser


class CollectionMeiliResultElements(BaseModel):
    id: UUID
    name: str
    author: CollectionMeiliResultElementsAuthor


class CollectionMeiliResultKeyClient(BaseModel):
    id: UUID


class CollectionMeiliResultKey(BaseModel):
    client: CollectionMeiliResultKeyClient


class CollectionMeiliResult(BaseModel):
    key: CollectionMeiliResultKey
    grouping: list[str]
    elements: list[CollectionMeiliResultElements]


adapter = TypeAdapter(list[CollectionMeiliResult])


async def collection_meili(
    executor: AsyncIOExecutor,
) -> list[CollectionMeiliResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
