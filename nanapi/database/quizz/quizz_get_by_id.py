from datetime import datetime
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id
select quizz::Quizz {
  *,
  author: {
    discord_id,
  },
}
filter .id = id;
"""


class QuizzGetByIdResultAuthor(BaseModel):
    discord_id: str


class QuizzGetByIdResult(BaseModel):
    author: QuizzGetByIdResultAuthor
    id: UUID
    channel_id: str
    answer: str | None
    submitted_at: datetime
    question: str | None
    hints: list[str] | None
    attachment_url: str | None


adapter = TypeAdapter(QuizzGetByIdResult | None)


async def quizz_get_by_id(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
) -> QuizzGetByIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
