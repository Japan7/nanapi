from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  message_id := <int64>$message_id
delete quizz::Game
filter .message_id = message_id
"""


class GameDeleteByMessageIdResult(BaseModel):
    id: UUID


adapter = TypeAdapter(GameDeleteByMessageIdResult | None)


async def game_delete_by_message_id(
    executor: AsyncIOExecutor,
    *,
    message_id: int,
) -> GameDeleteByMessageIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        message_id=message_id,
    )
    return adapter.validate_json(resp, strict=False)
