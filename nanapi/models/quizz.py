from uuid import UUID

from pydantic import BaseModel


class NewQuizzBody(BaseModel):
    channel_id: str
    description: str
    url: str | None = None
    is_image: bool
    author_discord_id: str
    author_discord_username: str


class SetQuizzAnswerBody(BaseModel):
    answer: str | None = None
    answer_source: str | None = None


class NewGameBody(BaseModel):
    message_id: str
    answer_bananed: str | None = None
    quizz_id: UUID


class SetGameBananedAnswerBody(BaseModel):
    answer_bananed: str | None = None


class EndGameBody(BaseModel):
    winner_discord_id: str
    winner_discord_username: str
