from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  role_id := <str>$role_id,
delete role::Role
filter .client = global client and .role_id = role_id
"""


class RoleDeleteByRoleIdResult(BaseModel):
    id: UUID


adapter = TypeAdapter(RoleDeleteByRoleIdResult | None)


async def role_delete_by_role_id(
    executor: AsyncIOExecutor,
    *,
    role_id: str,
) -> RoleDeleteByRoleIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        role_id=role_id,
    )
    return adapter.validate_json(resp, strict=False)
