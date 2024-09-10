from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  participant_id := <int64>$participant_id,
  participant_username := <str>$participant_username,
  participant := (
    insert user::User {
      discord_id := participant_id,
      discord_username := participant_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := participant_username,
      }
    )
  ),
update calendar::GuildEvent
filter .client = global client and .discord_id = discord_id
set {
  participants += participant,
};
"""


class GuildEventParticipantAddResult(BaseModel):
    id: UUID


adapter = TypeAdapter(GuildEventParticipantAddResult | None)


async def guild_event_participant_add(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    participant_id: int,
    participant_username: str,
) -> GuildEventParticipantAddResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        participant_id=participant_id,
        participant_username=participant_username,
    )
    return adapter.validate_json(resp, strict=False)
