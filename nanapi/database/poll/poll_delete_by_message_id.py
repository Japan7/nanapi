from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
delete poll::Poll filter .message_id = <int64>$message_id
"""


class PollDeleteByMessageIdResult(BaseModel):
    id: UUID


adapter = TypeAdapter(PollDeleteByMessageIdResult | None)


async def poll_delete_by_message_id(
    executor: AsyncIOExecutor,
    *,
    message_id: int,
) -> PollDeleteByMessageIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        message_id=message_id,
    )
    return adapter.validate_json(resp, strict=False)
