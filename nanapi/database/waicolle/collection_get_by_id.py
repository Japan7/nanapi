from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
select waicolle::Collection {
  id,
  name,
  author: {
    user: {
      discord_id,
    },
  },
  medias_ids_al := .items[is anilist::Media].id_al,
  staffs_ids_al := .items[is anilist::Staff].id_al,
  characters_ids_al := .characters.id_al,
}
filter .id = id
"""


class CollectionGetByIdResultAuthorUser(BaseModel):
    discord_id: str


class CollectionGetByIdResultAuthor(BaseModel):
    user: CollectionGetByIdResultAuthorUser


class CollectionGetByIdResult(BaseModel):
    id: UUID
    name: str
    author: CollectionGetByIdResultAuthor
    medias_ids_al: list[int]
    staffs_ids_al: list[int]
    characters_ids_al: list[int]


adapter = TypeAdapter(CollectionGetByIdResult | None)


async def collection_get_by_id(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
) -> CollectionGetByIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
