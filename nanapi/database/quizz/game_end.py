from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  winner_discord_id := <int64>$winner_discord_id,
  winner_discord_username := <str>$winner_discord_username,
  winner := (
    insert user::User {
      discord_id := winner_discord_id,
      discord_username := winner_discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := winner_discord_username,
      }
    )
  ),
  updated := (
    update quizz::Game
    filter .id = id
    set {
      status := quizz::Status.ENDED,
      ended_at := datetime_current(),
      winner := winner,
    }
  )
select updated {
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


class GameEndResultQuizzAuthor(BaseModel):
    discord_id: int
    discord_id_str: str


class GameEndResultQuizz(BaseModel):
    author: GameEndResultQuizzAuthor
    id: UUID
    channel_id: int
    answer: str | None
    channel_id_str: str
    question: str | None
    attachment_url: str | None
    submitted_at: datetime
    hints: list[str] | None


class GameEndResultWinner(BaseModel):
    discord_id: int
    discord_id_str: str


class GameEndResult(BaseModel):
    winner: GameEndResultWinner | None
    quizz: GameEndResultQuizz
    status: QuizzStatus
    started_at: datetime
    message_id_str: str
    ended_at: datetime | None
    message_id: int
    id: UUID


adapter = TypeAdapter(GameEndResult | None)


async def game_end(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    winner_discord_id: int,
    winner_discord_username: str,
) -> GameEndResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        winner_discord_id=winner_discord_id,
        winner_discord_username=winner_discord_username,
    )
    return adapter.validate_json(resp, strict=False)
