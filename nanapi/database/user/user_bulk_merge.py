from typing import Any
from uuid import UUID

import orjson
from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  users := <json>$users,
for user in json_array_unpack(users) union (
  with
    discord_id := <int64>json_get(user, 'discord_id'),
    discord_username := <str>json_get(user, 'discord_username'),
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
)
"""


class UserBulkMergeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(list[UserBulkMergeResult])


async def user_bulk_merge(
    executor: AsyncIOExecutor,
    *,
    users: Any,
) -> list[UserBulkMergeResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        users=orjson.dumps(users).decode(),
    )
    return adapter.validate_json(resp, strict=False)
