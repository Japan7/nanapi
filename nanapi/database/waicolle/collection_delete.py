from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
delete waicolle::Collection
filter .id = id
"""


class CollectionDeleteResult(BaseModel):
    id: UUID


adapter = TypeAdapter(CollectionDeleteResult | None)


async def collection_delete(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
) -> CollectionDeleteResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
