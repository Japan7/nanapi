from uuid import UUID

from pydantic import BaseModel, Field


class NewClientBody(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


class WhoamiResponse(BaseModel):
    id: UUID
    username: str
