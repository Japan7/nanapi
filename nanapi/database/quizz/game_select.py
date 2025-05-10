from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  status := <quizz::Status>$status,
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
filter .client = global client and .status = status
"""


GAME_SELECT_STATUS = Literal[
    'STARTED',
    'ENDED',
]


class QuizzStatus(StrEnum):
    STARTED = 'STARTED'
    ENDED = 'ENDED'


class GameSelectResultQuizzAuthor(BaseModel):
    discord_id: int
    discord_id_str: str


class GameSelectResultQuizz(BaseModel):
    author: GameSelectResultQuizzAuthor
    id: UUID
    channel_id: int
    answer: str | None
    channel_id_str: str
    question: str | None
    attachment_url: str | None
    submitted_at: datetime
    hints: list[str] | None


class GameSelectResultWinner(BaseModel):
    discord_id: int
    discord_id_str: str


class GameSelectResult(BaseModel):
    winner: GameSelectResultWinner | None
    quizz: GameSelectResultQuizz
    id: UUID
    message_id: int
    ended_at: datetime | None
    message_id_str: str
    started_at: datetime
    status: QuizzStatus


adapter = TypeAdapter(list[GameSelectResult])


async def game_select(
    executor: AsyncIOExecutor,
    *,
    status: GAME_SELECT_STATUS,
) -> list[GameSelectResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        status=status,
    )
    return adapter.validate_json(resp, strict=False)
