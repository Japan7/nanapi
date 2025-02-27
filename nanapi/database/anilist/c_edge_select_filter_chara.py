from enum import StrEnum

from gel import AsyncIOExecutor
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
filter .character.id_al = id_al
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


class CEdgeSelectFilterCharaResultVoiceActors(BaseModel):
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


class CEdgeSelectFilterCharaResultMedia(BaseModel):
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


class CEdgeSelectFilterCharaResult(BaseModel):
    character_role: AnilistCharacterRole
    media: CEdgeSelectFilterCharaResultMedia
    voice_actors: list[CEdgeSelectFilterCharaResultVoiceActors]


adapter = TypeAdapter(list[CEdgeSelectFilterCharaResult])


async def c_edge_select_filter_chara(
    executor: AsyncIOExecutor,
    *,
    id_al: int,
) -> list[CEdgeSelectFilterCharaResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
