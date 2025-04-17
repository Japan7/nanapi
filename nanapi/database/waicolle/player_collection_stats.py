from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  id := <uuid>$id,
  collec := (select waicolle::Collection filter .id = id),
  charas := (
    select collec.characters
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
  collection := assert_exists(collec) {
    id,
    name,
    author: {
      user: {
        discord_id,
      },
    },
    medias := .items[is anilist::Media] {
      type,
      id_al,
      title_user_preferred,
    },
    staffs := .items[is anilist::Staff] {
      id_al,
      name_user_preferred,
      name_native,
    },
  },
  nb_charas := nb_charas,
  nb_owned := nb_owned,
}
"""


class AnilistMediaType(StrEnum):
    ANIME = 'ANIME'
    MANGA = 'MANGA'


class PlayerCollectionStatsResultCollectionStaffs(BaseModel):
    id_al: int
    name_user_preferred: str
    name_native: str | None


class PlayerCollectionStatsResultCollectionMedias(BaseModel):
    type: AnilistMediaType
    id_al: int
    title_user_preferred: str


class PlayerCollectionStatsResultCollectionAuthorUser(BaseModel):
    discord_id: str


class PlayerCollectionStatsResultCollectionAuthor(BaseModel):
    user: PlayerCollectionStatsResultCollectionAuthorUser


class PlayerCollectionStatsResultCollection(BaseModel):
    id: UUID
    name: str
    author: PlayerCollectionStatsResultCollectionAuthor
    medias: list[PlayerCollectionStatsResultCollectionMedias]
    staffs: list[PlayerCollectionStatsResultCollectionStaffs]


class PlayerCollectionStatsResult(BaseModel):
    collection: PlayerCollectionStatsResultCollection
    nb_charas: int
    nb_owned: int


adapter = TypeAdapter(PlayerCollectionStatsResult)


async def player_collection_stats(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    id: UUID,
) -> PlayerCollectionStatsResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
