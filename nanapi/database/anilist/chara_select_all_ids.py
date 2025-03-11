from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select anilist::Character { id_al, last_update }
order by .last_update
"""


class CharaSelectAllIdsResult(BaseModel):
    id_al: int
    last_update: int


adapter = TypeAdapter(list[CharaSelectAllIdsResult])


async def chara_select_all_ids(
    executor: AsyncIOExecutor,
) -> list[CharaSelectAllIdsResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
