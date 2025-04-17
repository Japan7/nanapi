from datetime import datetime
from enum import StrEnum
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  winner_discord_id := <str>$winner_discord_id,
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


class GameEndResultQuizzAuthor(BaseModel):
    discord_id: str


class GameEndResultQuizz(BaseModel):
    id: UUID
    channel_id: str
    description: str | None
    url: str | None
    is_image: bool
    answer: str | None
    answer_source: str | None
    submitted_at: datetime
    hikaried: bool | None
    author: GameEndResultQuizzAuthor


class GameEndResultWinner(BaseModel):
    discord_id: str


class GameEndResult(BaseModel):
    id: UUID
    status: QuizzStatus
    message_id: str
    answer_bananed: str | None
    started_at: datetime
    ended_at: datetime | None
    winner: GameEndResultWinner | None
    quizz: GameEndResultQuizz


adapter = TypeAdapter(GameEndResult | None)


async def game_end(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    winner_discord_id: str,
    winner_discord_username: str,
) -> GameEndResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        winner_discord_id=winner_discord_id,
        winner_discord_username=winner_discord_username,
    )
    return adapter.validate_json(resp, strict=False)
