from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  id_al := <int32>$id_al,
  media := (select anilist::Media filter .id_al = id_al),
  _update := (
    update waicolle::Collection
    filter .id = id
    set {
      items += media,
    }
  ),
select {
  collection := assert_exists(_update) {
    id,
    name,
  },
  media := assert_exists(media) {
    id_al,
    type,
    title_user_preferred,
  },
}
"""


class AnilistMediaType(StrEnum):
    ANIME = 'ANIME'
    MANGA = 'MANGA'


class CollectionAddMediaResultMedia(BaseModel):
    id_al: int
    type: AnilistMediaType
    title_user_preferred: str


class CollectionAddMediaResultCollection(BaseModel):
    id: UUID
    name: str


class CollectionAddMediaResult(BaseModel):
    collection: CollectionAddMediaResultCollection
    media: CollectionAddMediaResultMedia


adapter = TypeAdapter(CollectionAddMediaResult)


async def collection_add_media(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    id_al: int,
) -> CollectionAddMediaResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
