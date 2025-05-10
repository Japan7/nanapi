from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  channel_id := <int64>$channel_id,
select quizz::Game {
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
filter .client = global client and .quizz.channel_id = channel_id and .status = quizz::Status.ENDED
order by .ended_at desc
limit 1
"""


class QuizzStatus(StrEnum):
    STARTED = 'STARTED'
    ENDED = 'ENDED'


class GameGetLastResultQuizzAuthor(BaseModel):
    discord_id: int
    discord_id_str: str


class GameGetLastResultQuizz(BaseModel):
    author: GameGetLastResultQuizzAuthor
    id: UUID
    channel_id: int
    answer: str | None
    channel_id_str: str
    question: str | None
    attachment_url: str | None
    submitted_at: datetime
    hints: list[str] | None


class GameGetLastResultWinner(BaseModel):
    discord_id: int
    discord_id_str: str


class GameGetLastResult(BaseModel):
    winner: GameGetLastResultWinner | None
    quizz: GameGetLastResultQuizz
    id: UUID
    message_id: int
    ended_at: datetime | None
    message_id_str: str
    started_at: datetime
    status: QuizzStatus


adapter = TypeAdapter(GameGetLastResult | None)


async def game_get_last(
    executor: AsyncIOExecutor,
    *,
    channel_id: int,
) -> GameGetLastResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        channel_id=channel_id,
    )
    return adapter.validate_json(resp, strict=False)
