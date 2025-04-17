from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  message_id := <str>$message_id,
  answer_bananed := <optional str>$answer_bananed,
  quizz_id := <uuid>$quizz_id,
  quizz := (select quizz::Quizz filter .id = quizz_id),
insert quizz::Game {
  client := global client,
  message_id := message_id,
  answer_bananed := answer_bananed,
  quizz := quizz,
}
"""


class GameNewResult(BaseModel):
    id: UUID


adapter = TypeAdapter(GameNewResult)


async def game_new(
    executor: AsyncIOExecutor,
    *,
    message_id: str,
    quizz_id: UUID,
    answer_bananed: str | None = None,
) -> GameNewResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        message_id=message_id,
        quizz_id=quizz_id,
        answer_bananed=answer_bananed,
    )
    return adapter.validate_json(resp, strict=False)
