from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  channel_id := <str>$channel_id,
  games := (
    select quizz::Game
    filter .client = global client and .quizz.channel_id = channel_id and .status = quizz::Status.STARTED
  )
select assert_single(games) {
  id,
  status,
  message_id,
  answer_bananed,
  started_at,
  ended_at,
  winner: {
    discord_id,
  },
  quizz: {
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
}
"""


class QuizzStatus(StrEnum):
    STARTED = 'STARTED'
    ENDED = 'ENDED'


class GameGetCurrentResultQuizzAuthor(BaseModel):
    discord_id: str


class GameGetCurrentResultQuizz(BaseModel):
    id: UUID
    channel_id: str
    description: str | None
    url: str | None
    is_image: bool
    answer: str | None
    answer_source: str | None
    submitted_at: datetime
    hikaried: bool | None
    author: GameGetCurrentResultQuizzAuthor


class GameGetCurrentResultWinner(BaseModel):
    discord_id: str


class GameGetCurrentResult(BaseModel):
    id: UUID
    status: QuizzStatus
    message_id: str
    answer_bananed: str | None
    started_at: datetime
    ended_at: datetime | None
    winner: GameGetCurrentResultWinner | None
    quizz: GameGetCurrentResultQuizz


adapter = TypeAdapter(GameGetCurrentResult | None)


async def game_get_current(
    executor: AsyncIOExecutor,
    *,
    channel_id: str,
) -> GameGetCurrentResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        channel_id=channel_id,
    )
    return adapter.validate_json(resp, strict=False)
