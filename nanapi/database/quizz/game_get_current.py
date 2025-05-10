from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  channel_id := <int64>$channel_id,
  games := (
    select quizz::Game
    filter .client = global client and .quizz.channel_id = channel_id and .status = quizz::Status.STARTED
  )
select assert_single(games) {
  *,
  winner: {
    discord_id,
    discord_id_str,
  },
  quizz: {
    *,
    author: {
      discord_id,
      discord_id_str,
    },
  }
}
"""


class QuizzStatus(StrEnum):
    STARTED = 'STARTED'
    ENDED = 'ENDED'


class GameGetCurrentResultQuizzAuthor(BaseModel):
    discord_id: int
    discord_id_str: str


class GameGetCurrentResultQuizz(BaseModel):
    author: GameGetCurrentResultQuizzAuthor
    id: UUID
    channel_id: int
    answer: str | None
    channel_id_str: str
    question: str | None
    attachment_url: str | None
    submitted_at: datetime
    hints: list[str] | None


class GameGetCurrentResultWinner(BaseModel):
    discord_id: int
    discord_id_str: str


class GameGetCurrentResult(BaseModel):
    winner: GameGetCurrentResultWinner | None
    quizz: GameGetCurrentResultQuizz
    id: UUID
    message_id: int
    ended_at: datetime | None
    message_id_str: str
    started_at: datetime
    status: QuizzStatus


adapter = TypeAdapter(GameGetCurrentResult | None)


async def game_get_current(
    executor: AsyncIOExecutor,
    *,
    channel_id: int,
) -> GameGetCurrentResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        channel_id=channel_id,
    )
    return adapter.validate_json(resp, strict=False)
