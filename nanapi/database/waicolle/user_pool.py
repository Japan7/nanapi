from enum import StrEnum

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <optional str>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  anilist := (select anilist::Account filter .user.discord_id = discord_id),
  pool := (
    select anilist::Character
    filter (
      ((
        .edges.media.entries.account = anilist
        if exists anilist else true
      ) or (
        (.id_al in player.tracked_characters.id_al)
        if exists player else true
      ))
      and
      (.image_large not ilike '%/default.jpg')
    )
  ),
  genred := (
    select pool
    filter (
      re_test(r"(?i)\y(?:female|non-binary)\y", .fuzzy_gender)
      if player.game_mode = waicolle::GameMode.WAIFU else
      re_test(r"(?i)\y(?:male|non-binary)\y", .fuzzy_gender)
      if player.game_mode = waicolle::GameMode.HUSBANDO else
      true
    )
  ) if exists player else pool
group genred {
  id_al,
}
by .rank
"""


class WaicolleRank(StrEnum):
    S = 'S'
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'
    E = 'E'


class UserPoolResultElements(BaseModel):
    id_al: int


class UserPoolResultKey(BaseModel):
    rank: WaicolleRank


class UserPoolResult(BaseModel):
    key: UserPoolResultKey
    grouping: list[str]
    elements: list[UserPoolResultElements]


adapter = TypeAdapter(list[UserPoolResult])


async def user_pool(
    executor: AsyncIOExecutor,
    *,
    discord_id: str | None = None,
) -> list[UserPoolResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
