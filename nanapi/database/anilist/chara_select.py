from enum import StrEnum

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  ids_al := <array<int32>>$ids_al
select anilist::Character {
  id_al,
  favourites,
  site_url,
  name_user_preferred,
  name_alternative,
  name_alternative_spoiler,
  name_native,
  description,
  image_large,
  gender,
  age,
  date_of_birth_year,
  date_of_birth_month,
  date_of_birth_day,
  rank,
  fuzzy_gender,
} filter .id_al in array_unpack(ids_al)
"""


class WaicolleRank(StrEnum):
    S = 'S'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'


class CharaSelectResult(BaseModel):
    id_al: int
    favourites: int
    site_url: str
    name_user_preferred: str
    name_alternative: list[str]
    name_alternative_spoiler: list[str]
    name_native: str | None
    description: str | None
    image_large: str
    gender: str | None
    age: str | None
    date_of_birth_year: int | None
    date_of_birth_month: int | None
    date_of_birth_day: int | None
    rank: WaicolleRank
    fuzzy_gender: str | None


adapter = TypeAdapter(list[CharaSelectResult])


async def chara_select(
    executor: AsyncIOExecutor,
    *,
    ids_al: list[int],
) -> list[CharaSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        ids_al=ids_al,
    )
    return adapter.validate_json(resp, strict=False)
