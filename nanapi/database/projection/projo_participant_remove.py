from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  participant_id := <str>$participant_id,
update projection::Projection
filter .id = id
set {
  participants -= (select user::User filter .discord_id = participant_id),
};
"""


class ProjoParticipantRemoveResult(BaseModel):
    id: UUID


adapter = TypeAdapter(ProjoParticipantRemoveResult | None)


async def projo_participant_remove(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    participant_id: str,
) -> ProjoParticipantRemoveResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        participant_id=participant_id,
    )
    return adapter.validate_json(resp, strict=False)
