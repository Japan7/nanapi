from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select calendar::UserCalendar { ** }
"""


class UserCalendarSelectAllResultUser(BaseModel):
    id: UUID
    discord_id: int
    discord_id_str: str
    discord_username: str


class UserCalendarSelectAllResult(BaseModel):
    id: UUID
    ics: str
    user: UserCalendarSelectAllResultUser


adapter = TypeAdapter(list[UserCalendarSelectAllResult])


async def user_calendar_select_all(
    executor: AsyncIOExecutor,
) -> list[UserCalendarSelectAllResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
