from pydantic import BaseModel


class UpdateMessageNoindexBody(BaseModel):
    noindex: str
