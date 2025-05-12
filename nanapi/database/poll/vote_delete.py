from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  message_id := <str>$message_id,
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
    discord_id: str,
    message_id: str,
) -> VoteDeleteResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        message_id=message_id,
    )
    return adapter.validate_json(resp, strict=False)
