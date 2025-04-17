from pydantic import BaseModel


class NewRoleBody(BaseModel):
    role_id: str
    emoji: str
