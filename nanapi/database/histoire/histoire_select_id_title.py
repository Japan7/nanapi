from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select histoire::Histoire { id, title }
filter .client = global client
"""


class HistoireSelectIdTitleResult(BaseModel):
    id: UUID
    title: str


adapter = TypeAdapter(list[HistoireSelectIdTitleResult])


async def histoire_select_id_title(
    executor: AsyncIOExecutor,
) -> list[HistoireSelectIdTitleResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
