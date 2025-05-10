from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <optional uuid>$id,
  status := <optional projection::Status>$status,
  message_id := <optional int64>$message_id,
  channel_id := <optional int64>$channel_id,
  all_projos := (select projection::Projection filter .client = global client),
  filtered := (
    (select all_projos filter .id = id)
    if exists id else
    (select all_projos filter .status = status and .channel_id = channel_id)
    if exists status and exists channel_id else
    (select all_projos filter .status = status)
    if exists status else
    (select all_projos filter .message_id = message_id)
    if exists message_id else
    (select all_projos filter .channel_id = channel_id)
    if exists channel_id else
    (select all_projos)
  )
select filtered {
  *,
  medias: {
    id_al,
    title_user_preferred,
    @added,
  } order by @added,
  external_medias: {
    id,
    title,
    @added,
  } order by @added,
  participants: { * },
  guild_events: { * },
}
"""


PROJO_SELECT_STATUS = Literal[
    'ONGOING',
    'COMPLETED',
]


class ProjectionStatus(StrEnum):
    ONGOING = 'ONGOING'
    COMPLETED = 'COMPLETED'


class ProjoSelectResultGuildEvents(BaseModel):
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


class ProjoSelectResultParticipants(BaseModel):
    id: UUID
    discord_id: int
    discord_id_str: str
    discord_username: str


class ProjoSelectResultExternalMedias(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: UUID
    title: str
    link_added: datetime | None = Field(validation_alias='@added', serialization_alias='@added')


class ProjoSelectResultMedias(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id_al: int
    title_user_preferred: str
    link_added: datetime | None = Field(validation_alias='@added', serialization_alias='@added')


class ProjoSelectResult(BaseModel):
    medias: list[ProjoSelectResultMedias]
    external_medias: list[ProjoSelectResultExternalMedias]
    participants: list[ProjoSelectResultParticipants]
    guild_events: list[ProjoSelectResultGuildEvents]
    status: ProjectionStatus
    name: str
    message_id_str: str | None
    message_id: int | None
    channel_id_str: str
    channel_id: int
    id: UUID


adapter = TypeAdapter(list[ProjoSelectResult])


async def projo_select(
    executor: AsyncIOExecutor,
    *,
    id: UUID | None = None,
    status: PROJO_SELECT_STATUS | None = None,
    message_id: int | None = None,
    channel_id: int | None = None,
) -> list[ProjoSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        id=id,
        status=status,
        message_id=message_id,
        channel_id=channel_id,
    )
    return adapter.validate_json(resp, strict=False)
