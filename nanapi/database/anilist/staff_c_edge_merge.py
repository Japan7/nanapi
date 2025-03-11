from typing import Any
from uuid import UUID

import orjson
from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  staff := <int32>$staff,
  characters := <json>$characters,
for edge in json_array_unpack(characters) union (
  with
    voice_actor_ids := <array<int32>>json_get(edge, 'voice_actor_ids'),
    character_id := <int32>json_get(edge, 'character_id'),
    media_id := <int32>json_get(edge, 'media_id'),
    character_role := <anilist::CharacterRole>json_get(edge, 'character_role'),
    voice_actor := (select anilist::Staff filter .id_al in array_unpack(voice_actor_ids)),
    character := (select anilist::Character filter .id_al = character_id),
    media := (select anilist::Media filter .id_al = media_id),
  insert anilist::CharacterEdge {
    character_role := character_role,
    character := character,
    media := media,
    voice_actors := voice_actor,
  }
  unless conflict on ((.character, .media)) else (
    update anilist::CharacterEdge set {
      character_role := character_role,
      voice_actors += voice_actor,
    }
  )
)
"""


class StaffCEdgeMergeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(list[StaffCEdgeMergeResult])


async def staff_c_edge_merge(
    executor: AsyncIOExecutor,
    *,
    staff: int,
    characters: Any,
) -> list[StaffCEdgeMergeResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        staff=staff,
        characters=orjson.dumps(characters).decode(),
    )
    return adapter.validate_json(resp, strict=False)
