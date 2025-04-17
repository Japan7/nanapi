from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  id_al := <int32>$id_al,
  media := (select anilist::Media filter .id_al = id_al),
  _update := (
    update waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
    set {
      tracked_items += media,
    }
  )
select {
  player := assert_exists(_update),
  media := assert_exists(media) {
    id_al,
    type,
    title_user_preferred,
  },
}
"""


class AnilistMediaType(StrEnum):
    ANIME = 'ANIME'
    MANGA = 'MANGA'


class PlayerAddMediaResultMedia(BaseModel):
    id_al: int
    type: AnilistMediaType
    title_user_preferred: str


class PlayerAddMediaResultPlayer(BaseModel):
    id: UUID


class PlayerAddMediaResult(BaseModel):
    player: PlayerAddMediaResultPlayer
    media: PlayerAddMediaResultMedia


adapter = TypeAdapter(PlayerAddMediaResult)


async def player_add_media(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    id_al: int,
) -> PlayerAddMediaResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
