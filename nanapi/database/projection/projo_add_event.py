from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  event_discord_id := <int64>$event_discord_id,
  event := (
    select calendar::GuildEvent
    filter .client = global client and .discord_id = event_discord_id
  ),
update projection::Projection
filter .id = id
set {
  guild_events += assert_exists(event)
}
"""


class ProjoAddEventResult(BaseModel):
    id: UUID


adapter = TypeAdapter(ProjoAddEventResult | None)


async def projo_add_event(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    event_discord_id: int,
) -> ProjoAddEventResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        event_discord_id=event_discord_id,
    )
    return adapter.validate_json(resp, strict=False)
