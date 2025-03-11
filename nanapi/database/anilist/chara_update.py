from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  characters := <array<int32>>$characters,
  last_update := <int64>$last_update,
for character_id in array_unpack(characters) union (
  update anilist::Character
  filter .id_al = <int32>character_id
  set {
    last_update := last_update
  }
)
"""


class CharaUpdateResult(BaseModel):
    id: UUID


adapter = TypeAdapter(list[CharaUpdateResult])


async def chara_update(
    executor: AsyncIOExecutor,
    *,
    characters: list[int],
    last_update: int,
) -> list[CharaUpdateResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        characters=characters,
        last_update=last_update,
    )
    return adapter.validate_json(resp, strict=False)
