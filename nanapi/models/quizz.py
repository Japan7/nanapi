from uuid import UUID

from pydantic import BaseModel


class NewQuizzBody(BaseModel):
    channel_id: str
    question: str | None = None
    attachment_url: str | None = None
    answer: str | None = None
    hints: list[str] | None = None
    author_discord_id: str
    author_discord_username: str


class SetQuizzAnswerBody(BaseModel):
    answer: str | None = None
    hints: list[str] | None = None


class NewGameBody(BaseModel):
    message_id: str
    quizz_id: UUID


class EndGameBody(BaseModel):
    winner_discord_id: str
    winner_discord_username: str
