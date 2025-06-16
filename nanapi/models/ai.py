from pydantic import BaseModel


class InsertPromptBodyArgument(BaseModel):
    name: str
    description: str | None = None


class InsertPromptBody(BaseModel):
    name: str
    description: str | None = None
    prompt: str
    arguments: list[InsertPromptBodyArgument]
