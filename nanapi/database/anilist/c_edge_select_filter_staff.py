from enum import StrEnum

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id_al := <int32>$id_al,
select anilist::CharacterEdge {
  character_role,
  media: {
    id_al,
    favourites,
    site_url,
    type,
    id_mal,
    title_user_preferred,
    title_native,
    title_english,
    synonyms,
    description,
    status,
    season,
    season_year,
    episodes,
    duration,
    chapters,
    cover_image_extra_large,
    cover_image_color,
    popularity,
    is_adult,
    genres,
  },
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
}
filter .voice_actors.id_al = id_al
order by .media.popularity desc
"""


class AnilistCharacterRole(StrEnum):
    MAIN = 'MAIN'
    SUPPORTING = 'SUPPORTING'
    BACKGROUND = 'BACKGROUND'


class AnilistMediaType(StrEnum):
    ANIME = 'ANIME'
    MANGA = 'MANGA'


class AnilistMediaStatus(StrEnum):
    FINISHED = 'FINISHED'
    RELEASING = 'RELEASING'
    NOT_YET_RELEASED = 'NOT_YET_RELEASED'
    CANCELLED = 'CANCELLED'
    HIATUS = 'HIATUS'


class AnilistMediaSeason(StrEnum):
    WINTER = 'WINTER'
    SPRING = 'SPRING'
    SUMMER = 'SUMMER'
    FALL = 'FALL'


class WaicolleRank(StrEnum):
    S = 'S'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'


class CEdgeSelectFilterStaffResultCharacter(BaseModel):
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


class CEdgeSelectFilterStaffResultMedia(BaseModel):
    id_al: int
    favourites: int
    site_url: str
    type: AnilistMediaType
    id_mal: int | None
    title_user_preferred: str
    title_native: str | None
    title_english: str | None
    synonyms: list[str]
    description: str | None
    status: AnilistMediaStatus | None
    season: AnilistMediaSeason | None
    season_year: int | None
    episodes: int | None
    duration: int | None
    chapters: int | None
    cover_image_extra_large: str
    cover_image_color: str | None
    popularity: int
    is_adult: bool
    genres: list[str]


class CEdgeSelectFilterStaffResult(BaseModel):
    character_role: AnilistCharacterRole
    media: CEdgeSelectFilterStaffResultMedia
    character: CEdgeSelectFilterStaffResultCharacter


adapter = TypeAdapter(list[CEdgeSelectFilterStaffResult])


async def c_edge_select_filter_staff(
    executor: AsyncIOExecutor,
    *,
    id_al: int,
) -> list[CEdgeSelectFilterStaffResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
