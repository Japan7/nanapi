from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  ascended_id := <uuid>$ascended_id,
  ascended_from_ids := <array<uuid>>$ascended_from_ids,
  waifus := (select waicolle::Waifu filter .id in array_unpack(ascended_from_ids)),
update waicolle::Waifu
filter .id = ascended_id
set {
  ascended_from += waifus
}
"""


class WaifuUpdateAscendedFromResult(BaseModel):
    id: UUID


adapter = TypeAdapter(WaifuUpdateAscendedFromResult | None)


async def waifu_update_ascended_from(
    executor: AsyncIOExecutor,
    *,
    ascended_id: UUID,
    ascended_from_ids: list[UUID],
) -> WaifuUpdateAscendedFromResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        ascended_id=ascended_id,
        ascended_from_ids=ascended_from_ids,
    )
    return adapter.validate_json(resp, strict=False)
