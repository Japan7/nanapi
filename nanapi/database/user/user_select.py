from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select user::User {
  discord_id,
  discord_username,
}
"""


class UserSelectResult(BaseModel):
    discord_id: str
    discord_username: str


adapter = TypeAdapter(list[UserSelectResult])


async def user_select(
    executor: AsyncIOExecutor,
) -> list[UserSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
