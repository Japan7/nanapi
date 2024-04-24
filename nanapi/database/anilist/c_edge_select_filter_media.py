from enum import StrEnum

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id_al := <int32>$id_al,
select anilist::CharacterEdge {
  character_role,
  character: {
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
  },
  voice_actors: {
    id_al,
    favourites,
    site_url,
    name_user_preferred,
    name_native,
    name_alternative,
    description,
    image_large,
    gender,
    age,
    date_of_birth_year,
    date_of_birth_month,
    date_of_birth_day,
    date_of_death_year,
    date_of_death_month,
    date_of_death_day,
  } order by .favourites desc
}
filter .media.id_al = id_al
order by .media.popularity desc
"""


class AnilistCharacterRole(StrEnum):
    MAIN = 'MAIN'
    SUPPORTING = 'SUPPORTING'
    BACKGROUND = 'BACKGROUND'


class WaicolleRank(StrEnum):
    S = 'S'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'


class CEdgeSelectFilterMediaResultVoiceActors(BaseModel):
    id_al: int
    favourites: int
    site_url: str
    name_user_preferred: str
    name_native: str | None
    name_alternative: list[str]
    description: str | None
    image_large: str
    gender: str | None
    age: int | None
    date_of_birth_year: int | None
    date_of_birth_month: int | None
    date_of_birth_day: int | None
    date_of_death_year: int | None
    date_of_death_month: int | None
    date_of_death_day: int | None


class CEdgeSelectFilterMediaResultCharacter(BaseModel):
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


class CEdgeSelectFilterMediaResult(BaseModel):
    character_role: AnilistCharacterRole
    character: CEdgeSelectFilterMediaResultCharacter
    voice_actors: list[CEdgeSelectFilterMediaResultVoiceActors]


adapter = TypeAdapter(list[CEdgeSelectFilterMediaResult])


async def c_edge_select_filter_media(
    executor: AsyncIOExecutor,
    *,
    id_al: int,
) -> list[CEdgeSelectFilterMediaResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
