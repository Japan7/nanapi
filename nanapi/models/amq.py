from pydantic import BaseModel


class UpsertAMQAccountBody(BaseModel):
    discord_username: str
    username: str
