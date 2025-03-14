from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <optional int64>$discord_id,
  start_after := <optional datetime>$start_after,
select calendar::GuildEvent { ** }
filter .client = global client
and (.participants.discord_id = discord_id if exists discord_id else true)
and (.start_time > start_after if exists start_after else true)
"""


class ProjectionStatus(StrEnum):
    ONGOING = 'ONGOING'
    COMPLETED = 'COMPLETED'


class GuildEventSelectResultProjection(BaseModel):
    id: UUID
    channel_id: int
    message_id: int | None
    name: str
    status: ProjectionStatus
    channel_id_str: str
    message_id_str: str | None


class GuildEventSelectResultOrganizer(BaseModel):
    id: UUID
    discord_id: int
    discord_id_str: str
    discord_username: str


class GuildEventSelectResultParticipants(BaseModel):
    id: UUID
    discord_id: int
    discord_id_str: str
    discord_username: str


class GuildEventSelectResultClient(BaseModel):
    id: UUID
    password_hash: str
    username: str


class GuildEventSelectResult(BaseModel):
    id: UUID
    discord_id: int
    description: str | None
    discord_id_str: str
    end_time: datetime
    image: str | None
    location: str | None
    name: str
    start_time: datetime
    url: str | None
    client: GuildEventSelectResultClient
    participants: list[GuildEventSelectResultParticipants]
    organizer: GuildEventSelectResultOrganizer
    projection: GuildEventSelectResultProjection | None


adapter = TypeAdapter(list[GuildEventSelectResult])


async def guild_event_select(
    executor: AsyncIOExecutor,
    *,
    discord_id: int | None = None,
    start_after: datetime | None = None,
) -> list[GuildEventSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        start_after=start_after,
    )
    return adapter.validate_json(resp, strict=False)
