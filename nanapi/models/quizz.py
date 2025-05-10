from uuid import UUID

from pydantic import BaseModel


class NewQuizzBody(BaseModel):
    channel_id: int
    question: str | None = None
    attachment_url: str | None = None
    answer: str | None = None
    hints: list[str] | None = None
    author_discord_id: int
    author_discord_username: str


class SetQuizzAnswerBody(BaseModel):
    answer: str | None = None
    hints: list[str] | None = None


class NewGameBody(BaseModel):
    message_id: int
    quizz_id: UUID


class EndGameBody(BaseModel):
    winner_discord_id: int
    winner_discord_username: str
