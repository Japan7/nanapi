from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  message_id := <int64>$message_id,
  quizz_id := <uuid>$quizz_id,
  quizz := (select quizz::Quizz filter .id = quizz_id),
insert quizz::Game {
  client := global client,
  message_id := message_id,
  quizz := quizz,
}
"""


class GameNewResult(BaseModel):
    id: UUID


adapter = TypeAdapter(GameNewResult)


async def game_new(
    executor: AsyncIOExecutor,
    *,
    message_id: int,
    quizz_id: UUID,
) -> GameNewResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        message_id=message_id,
        quizz_id=quizz_id,
    )
    return adapter.validate_json(resp, strict=False)
