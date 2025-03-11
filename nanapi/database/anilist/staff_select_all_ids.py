from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select anilist::Staff { id_al, last_update }
order by .last_update
"""


class StaffSelectAllIdsResult(BaseModel):
    id_al: int
    last_update: int


adapter = TypeAdapter(list[StaffSelectAllIdsResult])


async def staff_select_all_ids(
    executor: AsyncIOExecutor,
) -> list[StaffSelectAllIdsResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
