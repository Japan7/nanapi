from typing import Literal
from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  discord_username := <str>$discord_username,
  game_mode := <waicolle::GameMode>$game_mode,
  user := (
    insert user::User {
      discord_id := discord_id,
      discord_username := discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := discord_username,
      }
    )
  ),
insert waicolle::Player {
  client := global client,
  game_mode := game_mode,
  user := user,
}
unless conflict on ((.client, .user))
else (
  update waicolle::Player set {
    game_mode := game_mode,
    frozen_at := {},
  }
)
"""


PLAYER_MERGE_GAME_MODE = Literal[
    'WAIFU',
    'HUSBANDO',
    'ALL',
]


class PlayerMergeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(PlayerMergeResult | None)


async def player_merge(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    discord_username: str,
    game_mode: PLAYER_MERGE_GAME_MODE,
) -> PlayerMergeResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        discord_username=discord_username,
        game_mode=game_mode,
    )
    return adapter.validate_json(resp, strict=False)
