from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  role_id := <str>$role_id,
  emoji := <str>$emoji,
  role := (
    insert role::Role {
      client := global client,
      role_id := role_id,
      emoji := emoji,
    }
  )
select role {
  role_id,
  emoji,
}
"""


class RoleInsertSelectResult(BaseModel):
    role_id: str
    emoji: str


adapter = TypeAdapter(RoleInsertSelectResult)


async def role_insert_select(
    executor: AsyncIOExecutor,
    *,
    role_id: str,
    emoji: str,
) -> RoleInsertSelectResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        role_id=role_id,
        emoji=emoji,
    )
    return adapter.validate_json(resp, strict=False)
