from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  participant_id := <int64>$participant_id,
update calendar::GuildEvent
filter .client = global client and .discord_id = discord_id
set {
  participants -= (select user::User filter .discord_id = participant_id),
};
"""


class GuildEventParticipantRemoveResult(BaseModel):
    id: UUID


adapter = TypeAdapter(GuildEventParticipantRemoveResult | None)


async def guild_event_participant_remove(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    participant_id: int,
) -> GuildEventParticipantRemoveResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        participant_id=participant_id,
    )
    return adapter.validate_json(resp, strict=False)
