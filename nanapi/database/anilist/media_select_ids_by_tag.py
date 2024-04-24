from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  tag_name := <str>$tag_name,
  min_rank := <int32>$min_rank,
select anilist::Media {
  id_al,
}
filter .tags.name = tag_name and .tags@rank >= min_rank
"""


class MediaSelectIdsByTagResult(BaseModel):
    id_al: int


adapter = TypeAdapter(list[MediaSelectIdsByTagResult])


async def media_select_ids_by_tag(
    executor: AsyncIOExecutor,
    *,
    tag_name: str,
    min_rank: int,
) -> list[MediaSelectIdsByTagResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        tag_name=tag_name,
        min_rank=min_rank,
    )
    return adapter.validate_json(resp, strict=False)
