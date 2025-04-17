from typing import Literal
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  service := <anilist::Service>$service,
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
insert anilist::Account {
  service := service,
  username := username,
  user := user,
}
unless conflict on .user
else (
  update anilist::Account set {
    service := service,
    username := username,
  }
)
"""


ACCOUNT_MERGE_SERVICE = Literal[
    'ANILIST',
    'MYANIMELIST',
]


class AccountMergeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(AccountMergeResult)


async def account_merge(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    discord_username: str,
    service: ACCOUNT_MERGE_SERVICE,
    username: str,
) -> AccountMergeResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        discord_username=discord_username,
        service=service,
        username=username,
    )
    return adapter.validate_json(resp, strict=False)
