from datetime import datetime
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  channel_id := <str>$channel_id
select quizz::Quizz {
  id,
  channel_id,
  description,
  url,
  is_image,
  answer,
  answer_source,
  submitted_at,
  hikaried,
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
    id: UUID
    channel_id: str
    description: str | None
    url: str | None
    is_image: bool
    answer: str | None
    answer_source: str | None
    submitted_at: datetime
    hikaried: bool | None
    author: QuizzGetOldestResultAuthor


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
