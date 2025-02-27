from typing import Any
from uuid import UUID

import orjson
from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  settings := <json>$settings,
for setting in json_object_unpack(settings) union (
  with
    key := <str>setting.0,
    value := <str>to_str(setting.1),
  insert amq::Setting {
    client := global client,
    key := key,
    value := value,
  }
  unless conflict on ((.client, .key))
  else (
    update amq::Setting set {
      value := value,
    }
  )
);
"""


class SettingsMergeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(list[SettingsMergeResult])


async def settings_merge(
    executor: AsyncIOExecutor,
    *,
    settings: Any,
) -> list[SettingsMergeResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        settings=orjson.dumps(settings).decode(),
    )
    return adapter.validate_json(resp, strict=False)
