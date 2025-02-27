from typing import Literal
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  type := <presence::PresenceType>$type,
  name := <str>$name,
insert presence::Presence {
  client := global client,
  type := type,
  name := name,
}
"""


PRESENCE_INSERT_TYPE = Literal[
    'PLAYING',
    'LISTENING',
    'WATCHING',
]


class PresenceInsertResult(BaseModel):
    id: UUID


adapter = TypeAdapter(PresenceInsertResult)


async def presence_insert(
    executor: AsyncIOExecutor,
    *,
    type: PRESENCE_INSERT_TYPE,
    name: str,
) -> PresenceInsertResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        type=type,
        name=name,
    )
    return adapter.validate_json(resp, strict=False)
