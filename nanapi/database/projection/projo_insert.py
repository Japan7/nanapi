from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  name := <str>$name,
  channel_id := <int64>$channel_id,
insert projection::Projection {
  client := global client,
  name := name,
  channel_id := channel_id,
}
"""


class ProjoInsertResult(BaseModel):
    id: UUID


adapter = TypeAdapter(ProjoInsertResult)


async def projo_insert(
    executor: AsyncIOExecutor,
    *,
    name: str,
    channel_id: int,
) -> ProjoInsertResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        name=name,
        channel_id=channel_id,
    )
    return adapter.validate_json(resp, strict=False)
