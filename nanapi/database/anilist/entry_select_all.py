from enum import StrEnum
from typing import Literal

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  media_type := <optional anilist::MediaType>$media_type,
  discord_id := <optional int64>$discord_id,
  entries := (
    (select anilist::Entry filter .account.user.discord_id = discord_id)
    if (exists discord_id) else
    (select anilist::Entry)
  ),
select entries {
  status,
  progress,
  score,
  media: {
    id_al,
  },
  account: {
    user: {
      discord_id,
      discord_id_str,
    },
  }
}
filter .media.type = media_type if exists media_type else true
"""


ENTRY_SELECT_ALL_MEDIA_TYPE = Literal[
    'ANIME',
    'MANGA',
]


class AnilistEntryStatus(StrEnum):
    CURRENT = 'CURRENT'
    COMPLETED = 'COMPLETED'
    PAUSED = 'PAUSED'
    DROPPED = 'DROPPED'
    PLANNING = 'PLANNING'
    REPEATING = 'REPEATING'


class EntrySelectAllResultAccountUser(BaseModel):
    discord_id: int
    discord_id_str: str


class EntrySelectAllResultAccount(BaseModel):
    user: EntrySelectAllResultAccountUser


class EntrySelectAllResultMedia(BaseModel):
    id_al: int


class EntrySelectAllResult(BaseModel):
    status: AnilistEntryStatus
    progress: int
    score: float
    media: EntrySelectAllResultMedia
    account: EntrySelectAllResultAccount


adapter = TypeAdapter(list[EntrySelectAllResult])


async def entry_select_all(
    executor: AsyncIOExecutor,
    *,
    media_type: ENTRY_SELECT_ALL_MEDIA_TYPE | None = None,
    discord_id: int | None = None,
) -> list[EntrySelectAllResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        media_type=media_type,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
