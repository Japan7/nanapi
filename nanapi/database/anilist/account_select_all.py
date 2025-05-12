from enum import StrEnum

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
select anilist::Account {
  service,
  username,
  user: {
    discord_id,
  },
}
"""


class AnilistService(StrEnum):
    ANILIST = 'ANILIST'
    MYANIMELIST = 'MYANIMELIST'


class AccountSelectAllResultUser(BaseModel):
    discord_id: str


class AccountSelectAllResult(BaseModel):
    service: AnilistService
    username: str
    user: AccountSelectAllResultUser


adapter = TypeAdapter(list[AccountSelectAllResult])


async def account_select_all(
    executor: AsyncIOExecutor,
) -> list[AccountSelectAllResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
