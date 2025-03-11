from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  event := (
    delete calendar::GuildEvent
    filter .client = global client and .discord_id = discord_id
  ),
select event { ** }
"""


class ProjectionStatus(StrEnum):
    ONGOING = 'ONGOING'
    COMPLETED = 'COMPLETED'


class GuildEventDeleteResultClient(BaseModel):
    id: UUID
    password_hash: str
    username: str


class GuildEventDeleteResultParticipants(BaseModel):
    id: UUID
    discord_id: int
    discord_id_str: str
    discord_username: str


class GuildEventDeleteResultOrganizer(BaseModel):
    id: UUID
    discord_id: int
    discord_id_str: str
    discord_username: str


class GuildEventDeleteResultProjection(BaseModel):
    id: UUID
    channel_id: int
    message_id: int | None
    name: str
    status: ProjectionStatus
    channel_id_str: str
    message_id_str: str | None


class GuildEventDeleteResult(BaseModel):
    url: str | None
    start_time: datetime
    name: str
    location: str | None
    image: str | None
    end_time: datetime
    discord_id_str: str
    description: str | None
    discord_id: int
    id: UUID
    projection: GuildEventDeleteResultProjection | None
    organizer: GuildEventDeleteResultOrganizer
    participants: list[GuildEventDeleteResultParticipants]
    client: GuildEventDeleteResultClient


adapter = TypeAdapter(GuildEventDeleteResult | None)


async def guild_event_delete(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
) -> GuildEventDeleteResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
