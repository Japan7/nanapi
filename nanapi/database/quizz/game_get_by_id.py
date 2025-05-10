from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
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
filter .id = id
"""


class QuizzStatus(StrEnum):
    STARTED = 'STARTED'
    ENDED = 'ENDED'


class GameGetByIdResultQuizzAuthor(BaseModel):
    discord_id: int
    discord_id_str: str


class GameGetByIdResultQuizz(BaseModel):
    author: GameGetByIdResultQuizzAuthor
    id: UUID
    channel_id: int
    answer: str | None
    channel_id_str: str
    question: str | None
    attachment_url: str | None
    submitted_at: datetime
    hints: list[str] | None


class GameGetByIdResultWinner(BaseModel):
    discord_id: int
    discord_id_str: str


class GameGetByIdResult(BaseModel):
    winner: GameGetByIdResultWinner | None
    quizz: GameGetByIdResultQuizz
    id: UUID
    message_id: int
    ended_at: datetime | None
    message_id_str: str
    started_at: datetime
    status: QuizzStatus


adapter = TypeAdapter(GameGetByIdResult | None)


async def game_get_by_id(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
) -> GameGetByIdResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
    )
    return adapter.validate_json(resp, strict=False)
