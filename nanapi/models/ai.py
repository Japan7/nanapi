from pydantic import BaseModel


class InsertSkillBody(BaseModel):
    name: str
    description: str
    content: str
