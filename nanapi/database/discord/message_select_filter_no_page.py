# Generated by gel-pydantic-codegen
# pyright: strict
from datetime import datetime
from typing import Any

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  channel_id := <str>$channel_id,
  tafter := <optional datetime>$after,
  n_offset := <optional int32>$offset,
  n_limit := <optional int32>$limit,
select discord::Message { data }
filter .client = global client
and not exists .pages
and not exists .deleted_at
and not exists .noindex
and .channel_id = channel_id
and (.timestamp > tafter if exists tafter else true)
order by .timestamp asc
offset n_offset
limit n_limit
"""


class MessageSelectFilterNoPageResult(BaseModel):
    data: Any


adapter = TypeAdapter[list[MessageSelectFilterNoPageResult]](list[MessageSelectFilterNoPageResult])


async def message_select_filter_no_page(
    executor: AsyncIOExecutor,
    *,
    channel_id: str,
    after: datetime | None = None,
    offset: int | None = None,
    limit: int | None = None,
) -> list[MessageSelectFilterNoPageResult]:
    resp = await executor.query_json(  # pyright: ignore[reportUnknownMemberType]
        EDGEQL_QUERY,
        channel_id=channel_id,
        after=after,
        offset=offset,
        limit=limit,
    )
    return adapter.validate_json(resp, strict=False)
