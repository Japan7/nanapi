from typing import Any

from pydantic import BaseModel, Json


class UpsertMessageBody(BaseModel):
    data: Json[Any]
