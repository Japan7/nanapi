from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  calendar := (select calendar::UserCalendar filter .user.discord_id = discord_id),
select assert_single(calendar) { ** }
"""


class UserCalendarSelectResultUser(BaseModel):
    id: UUID
    discord_id: str
    discord_username: str


class UserCalendarSelectResult(BaseModel):
    id: UUID
    ics: str
    user: UserCalendarSelectResultUser


adapter = TypeAdapter(UserCalendarSelectResult | None)


async def user_calendar_select(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
) -> UserCalendarSelectResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
