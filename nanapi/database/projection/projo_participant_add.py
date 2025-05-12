from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  participant_id := <str>$participant_id,
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
update projection::Projection
filter .id = id
set {
  participants += participant,
};
"""


class ProjoParticipantAddResult(BaseModel):
    id: UUID


adapter = TypeAdapter(ProjoParticipantAddResult | None)


async def projo_participant_add(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    participant_id: str,
    participant_username: str,
) -> ProjoParticipantAddResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        participant_id=participant_id,
        participant_username=participant_username,
    )
    return adapter.validate_json(resp, strict=False)
