from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select anilist::Character {
  id_al,
  name_user_preferred,
  name_alternative,
  name_alternative_spoiler,
  name_native
}
order by .favourites desc
"""


class CharaSelectAllNamesResult(BaseModel):
    id_al: int
    name_user_preferred: str
    name_alternative: list[str]
    name_alternative_spoiler: list[str]
    name_native: str | None


adapter = TypeAdapter(list[CharaSelectAllNamesResult])


async def chara_select_all_names(
    executor: AsyncIOExecutor,
) -> list[CharaSelectAllNamesResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
