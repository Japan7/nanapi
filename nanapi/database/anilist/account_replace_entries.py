from typing import Any, Literal
from uuid import UUID

import orjson
from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  service := <anilist::Service>$service,
  username := <str>$username,
  type := <anilist::MediaType>$type,
  account := (select anilist::Account filter .service = service and .username = username),
delete anilist::Entry
filter .account = account and .media.type = type;

with
  service := <anilist::Service>$service,
  username := <str>$username,
  entries := <json>$entries,
  account := (select anilist::Account filter .service = service and .username = username),
for entry in json_array_unpack(entries) union (
  with
    id_al := <int32>json_get(entry, 'id_al'),
    status := <anilist::EntryStatus>json_get(entry, 'status'),
    progress := <int32>json_get(entry, 'progress'),
    score := <float32>json_get(entry, 'score'),
    media := (select anilist::Media filter .id_al = id_al),
  insert anilist::Entry {
    status := status,
    progress := progress,
    score := score,
    account := account,
    media := media,
  }
);
"""


ACCOUNT_REPLACE_ENTRIES_SERVICE = Literal[
    'ANILIST',
    'MYANIMELIST',
]

ACCOUNT_REPLACE_ENTRIES_TYPE = Literal[
    'ANIME',
    'MANGA',
]


class AccountReplaceEntriesResult(BaseModel):
    id: UUID


adapter = TypeAdapter(list[AccountReplaceEntriesResult])


async def account_replace_entries(
    executor: AsyncIOExecutor,
    *,
    service: ACCOUNT_REPLACE_ENTRIES_SERVICE,
    username: str,
    type: ACCOUNT_REPLACE_ENTRIES_TYPE,
    entries: Any,
) -> list[AccountReplaceEntriesResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        service=service,
        username=username,
        type=type,
        entries=orjson.dumps(entries).decode(),
    )
    return adapter.validate_json(resp, strict=False)
