from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  id_al := <int32>$id_al,
update projection::Projection
filter .id = id
set {
  medias -= (select .medias filter .id_al = id_al),
}
"""


class ProjoRemoveMediaResult(BaseModel):
    id: UUID


adapter = TypeAdapter(ProjoRemoveMediaResult | None)


async def projo_remove_media(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    id_al: int,
) -> ProjoRemoveMediaResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
