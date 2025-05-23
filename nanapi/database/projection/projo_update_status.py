# Generated by gel-pydantic-codegen
# pyright: strict
from typing import Literal
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  status := <projection::Status>$status,
update projection::Projection
filter .id = id
set { status := status }
"""


PROJO_UPDATE_STATUS_STATUS = Literal[
    'ONGOING',
    'COMPLETED',
]


class ProjoUpdateStatusResult(BaseModel):
    id: UUID


adapter = TypeAdapter[ProjoUpdateStatusResult | None](ProjoUpdateStatusResult | None)


async def projo_update_status(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    status: PROJO_UPDATE_STATUS_STATUS,
) -> ProjoUpdateStatusResult | None:
    resp = await executor.query_single_json(  # pyright: ignore[reportUnknownMemberType]
        EDGEQL_QUERY,
        id=id,
        status=status,
    )
    return adapter.validate_json(resp, strict=False)
