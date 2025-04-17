from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  username := <optional str>$username,
  filtered := (
    (select amq::Account filter .username = username)
    if exists username else
    (select amq::Account)
  )
select filtered {
  username,
  user: {
    discord_id,
  }
}
"""


class AccountSelectResultUser(BaseModel):
    discord_id: str


class AccountSelectResult(BaseModel):
    username: str
    user: AccountSelectResultUser


adapter = TypeAdapter(list[AccountSelectResult])


async def account_select(
    executor: AsyncIOExecutor,
    *,
    username: str | None = None,
) -> list[AccountSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        username=username,
    )
    return adapter.validate_json(resp, strict=False)
