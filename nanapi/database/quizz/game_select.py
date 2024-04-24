from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  status := <quizz::Status>$status,
select quizz::Game {
  id,
  status,
  message_id,
  message_id_str,
  answer_bananed,
  started_at,
  ended_at,
  winner: {
    discord_id,
    discord_id_str,
  },
  quizz: {
    id,
    channel_id,
    channel_id_str,
    description,
    url,
    is_image,
    answer,
    answer_source,
    submitted_at,
    hikaried,
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
    id: UUID
    channel_id: int
    channel_id_str: str
    description: str | None
    url: str | None
    is_image: bool
    answer: str | None
    answer_source: str | None
    submitted_at: datetime
    hikaried: bool | None
    author: GameSelectResultQuizzAuthor


class GameSelectResultWinner(BaseModel):
    discord_id: int
    discord_id_str: str


class GameSelectResult(BaseModel):
    id: UUID
    status: QuizzStatus
    message_id: int
    message_id_str: str
    answer_bananed: str | None
    started_at: datetime
    ended_at: datetime | None
    winner: GameSelectResultWinner | None
    quizz: GameSelectResultQuizz


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
