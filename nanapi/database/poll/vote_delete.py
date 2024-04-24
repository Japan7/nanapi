from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  message_id := <int64>$message_id,
  _user := (select user::User filter .discord_id = discord_id),
  _poll := (select poll::Poll { options } filter .message_id = message_id),
delete poll::Vote
filter .poll = _poll and .user = _user
"""


class VoteDeleteResult(BaseModel):
    id: UUID


adapter = TypeAdapter(VoteDeleteResult | None)


async def vote_delete(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    message_id: int,
) -> VoteDeleteResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        message_id=message_id,
    )
    return adapter.validate_json(resp, strict=False)
