from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  message_id := <str>$message_id,
update projection::Projection
filter .id = id
set { message_id := message_id }
"""


class ProjoUpdateMessageIdResult(BaseModel):
    id: UUID


adapter = TypeAdapter(ProjoUpdateMessageIdResult | None)


async def projo_update_message_id(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    message_id: str,
) -> ProjoUpdateMessageIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        message_id=message_id,
    )
    return adapter.validate_json(resp, strict=False)
