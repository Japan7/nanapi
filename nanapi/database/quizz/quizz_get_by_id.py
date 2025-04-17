from datetime import datetime
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id
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
filter .id = id;
"""


class QuizzGetByIdResultAuthor(BaseModel):
    discord_id: str


class QuizzGetByIdResult(BaseModel):
    id: UUID
    channel_id: str
    description: str | None
    url: str | None
    is_image: bool
    answer: str | None
    answer_source: str | None
    submitted_at: datetime
    hikaried: bool | None
    author: QuizzGetByIdResultAuthor


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
