from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  answer := <optional str>$answer,
  hints := <optional array<str>>$hints,
update quizz::Quizz
filter .id = id
set {
  answer := answer,
  hints := hints,
}
"""


class QuizzSetAnswerResult(BaseModel):
    id: UUID


adapter = TypeAdapter(QuizzSetAnswerResult | None)


async def quizz_set_answer(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    answer: str | None = None,
    hints: list[str] | None = None,
) -> QuizzSetAnswerResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        answer=answer,
        hints=hints,
    )
    return adapter.validate_json(resp, strict=False)
