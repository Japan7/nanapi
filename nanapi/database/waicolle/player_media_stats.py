from enum import StrEnum

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  id_al := <int32>$id_al,
  media := (select anilist::Media filter .id_al = id_al),
  charas := (
    select media.character_edges.character
    filter (.image_large not ilike '%/default.jpg')
  ),
  nb_charas := count(charas),
  owned := (
    select waicolle::Waifu
    filter .client = global client
    and .owner = assert_exists(player)
    and .character in charas
    and not .disabled
  ),
  owned_ids := (select owned.character.id_al),
  nb_owned := count(owned_ids),
select {
  media := assert_exists(media) {
    type,
    id_al,
    title_user_preferred,
  },
  nb_charas := nb_charas,
  nb_owned := nb_owned,
}
"""


class AnilistMediaType(StrEnum):
    ANIME = 'ANIME'
    MANGA = 'MANGA'


class PlayerMediaStatsResultMedia(BaseModel):
    type: AnilistMediaType
    id_al: int
    title_user_preferred: str


class PlayerMediaStatsResult(BaseModel):
    media: PlayerMediaStatsResultMedia
    nb_charas: int
    nb_owned: int


adapter = TypeAdapter(PlayerMediaStatsResult)


async def player_media_stats(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    id_al: int,
) -> PlayerMediaStatsResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
