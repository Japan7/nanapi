from datetime import datetime
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  channel_id := <str>$channel_id,
  message := <str>$message,
  timestamp := <datetime>$timestamp,
  user := (
    insert user::User {
      discord_id := discord_id,
      discord_username := discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := discord_username,
      }
    )
  ),
  reminder := (
    insert reminder::Reminder {
      client := global client,
      channel_id := channel_id,
      message := message,
      timestamp := timestamp,
      user := user,
    }
  )
select reminder {
  id,
  channel_id,
  message,
  timestamp,
  user: {
    discord_id,
  },
};
"""


class ReminderInsertSelectResultUser(BaseModel):
    discord_id: str


class ReminderInsertSelectResult(BaseModel):
    id: UUID
    channel_id: str
    message: str
    timestamp: datetime
    user: ReminderInsertSelectResultUser


adapter = TypeAdapter(ReminderInsertSelectResult)


async def reminder_insert_select(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    discord_username: str,
    channel_id: str,
    message: str,
    timestamp: datetime,
) -> ReminderInsertSelectResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        discord_username=discord_username,
        channel_id=channel_id,
        message=message,
        timestamp=timestamp,
    )
    return adapter.validate_json(resp, strict=False)
