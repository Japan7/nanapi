from typing import Literal

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  season := <anilist::MediaSeason>$season,
  season_year := <int32>$season_year,
select anilist::Media {
  id_al,
}
filter .season = season and .season_year = season_year
"""


MEDIA_SELECT_IDS_BY_SEASON_SEASON = Literal[
    'WINTER',
    'SPRING',
    'SUMMER',
    'FALL',
]


class MediaSelectIdsBySeasonResult(BaseModel):
    id_al: int


adapter = TypeAdapter(list[MediaSelectIdsBySeasonResult])


async def media_select_ids_by_season(
    executor: AsyncIOExecutor,
    *,
    season: MEDIA_SELECT_IDS_BY_SEASON_SEASON,
    season_year: int,
) -> list[MediaSelectIdsBySeasonResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        season=season,
        season_year=season_year,
    )
    return adapter.validate_json(resp, strict=False)
