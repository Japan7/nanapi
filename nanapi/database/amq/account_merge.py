from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  username := <str>$username,
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
insert amq::Account {
  username := username,
  user := user,
}
unless conflict on .user
else (
  update amq::Account set {
    username := username,
  }
)
"""


class AccountMergeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(AccountMergeResult)


async def account_merge(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    discord_username: str,
    username: str,
) -> AccountMergeResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        discord_username=discord_username,
        username=username,
    )
    return adapter.validate_json(resp, strict=False)
