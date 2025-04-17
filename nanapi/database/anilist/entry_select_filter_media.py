from enum import StrEnum

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id_al := <int32>$id_al,
select anilist::Entry {
  status,
  progress,
  score,
  account: {
    user: {
      discord_id,
    },
  }
}
filter .media.id_al = id_al
"""


class AnilistEntryStatus(StrEnum):
    CURRENT = 'CURRENT'
    COMPLETED = 'COMPLETED'
    PAUSED = 'PAUSED'
    DROPPED = 'DROPPED'
    PLANNING = 'PLANNING'
    REPEATING = 'REPEATING'


class EntrySelectFilterMediaResultAccountUser(BaseModel):
    discord_id: str


class EntrySelectFilterMediaResultAccount(BaseModel):
    user: EntrySelectFilterMediaResultAccountUser


class EntrySelectFilterMediaResult(BaseModel):
    status: AnilistEntryStatus
    progress: int
    score: float
    account: EntrySelectFilterMediaResultAccount


adapter = TypeAdapter(list[EntrySelectFilterMediaResult])


async def entry_select_filter_media(
    executor: AsyncIOExecutor,
    *,
    id_al: int,
) -> list[EntrySelectFilterMediaResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
