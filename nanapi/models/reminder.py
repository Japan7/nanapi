from datetime import datetime

from pydantic import BaseModel


class NewReminderBody(BaseModel):
    discord_id: str
    discord_username: str
    channel_id: str
    message: str
    timestamp: datetime
