from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  ics := <str>$ics,
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
insert calendar::UserCalendar {
  ics := ics,
  user := user,
}
unless conflict on .user
else (
  update calendar::UserCalendar set {
    ics := ics,
  }
)
"""


class UserCalendarMergeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(UserCalendarMergeResult)


async def user_calendar_merge(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    discord_username: str,
    ics: str,
) -> UserCalendarMergeResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        discord_username=discord_username,
        ics=ics,
    )
    return adapter.validate_json(resp, strict=False)
