from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  discord_username := <str>$discord_username,
  message_id := <int64>$message_id,
  rank := <int32>$rank,
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
  poll := (select poll::Poll filter .message_id = message_id),
  option := (select poll::Option filter .poll = poll and .rank = rank),
insert poll::Vote {
  client := global client,
  poll := poll,
  option := option,
  user := user,
}
unless conflict on ((.poll, .user)) else (
  update poll::Vote set {
    option := option,
  }
)
"""


class VoteMergeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(VoteMergeResult | None)


async def vote_merge(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    discord_username: str,
    message_id: int,
    rank: int,
) -> VoteMergeResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        discord_username=discord_username,
        message_id=message_id,
        rank=rank,
    )
    return adapter.validate_json(resp, strict=False)
