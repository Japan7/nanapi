from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
update waicolle::TradeOperation
filter .id = id
set {
  completed_at := datetime_current(),
}
"""


class TradeCommitResult(BaseModel):
    id: UUID


adapter = TypeAdapter(TradeCommitResult | None)


async def trade_commit(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
) -> TradeCommitResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
