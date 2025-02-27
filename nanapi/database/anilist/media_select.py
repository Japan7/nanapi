from enum import StrEnum

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  ids_al := <array<int32>>$ids_al
select anilist::Media {
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
} filter .id_al in array_unpack(ids_al)
"""


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


class MediaSelectResult(BaseModel):
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


adapter = TypeAdapter(list[MediaSelectResult])


async def media_select(
    executor: AsyncIOExecutor,
    *,
    ids_al: list[int],
) -> list[MediaSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        ids_al=ids_al,
    )
    return adapter.validate_json(resp, strict=False)
