from datetime import datetime
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  channel_id := <str>$channel_id
select quizz::Quizz {
  *,
  author: {
    discord_id,
  },
}
filter .client = global client and not exists .game and .channel_id = channel_id
order by .submitted_at
limit 1
"""


class QuizzGetOldestResultAuthor(BaseModel):
    discord_id: str


class QuizzGetOldestResult(BaseModel):
    author: QuizzGetOldestResultAuthor
    id: UUID
    channel_id: str
    answer: str | None
    submitted_at: datetime
    question: str | None
    hints: list[str] | None
    attachment_url: str | None


adapter = TypeAdapter(QuizzGetOldestResult | None)


async def quizz_get_oldest(
    executor: AsyncIOExecutor,
    *,
    channel_id: str,
) -> QuizzGetOldestResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        channel_id=channel_id,
    )
    return adapter.validate_json(resp, strict=False)
