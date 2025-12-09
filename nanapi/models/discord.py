from pydantic import BaseModel

from nanapi.database.discord.rag_query import RagQueryResultObject


class UpdateMessageNoindexBody(BaseModel):
    noindex: str


class MessagesRagResult(BaseModel):
    object: RagQueryResultObject
    distance: float


class ReactionAddBody(BaseModel):
    animated: bool | None = None
    burst: bool | None = None
