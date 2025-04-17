from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  id_al := <int32>$id_al,
  staff := (select anilist::Staff filter .id_al = id_al),
update waicolle::Player
filter .client = global client and .user.discord_id = discord_id
set {
  tracked_items -= staff,
}
"""


class PlayerRemoveStaffResult(BaseModel):
    id: UUID


adapter = TypeAdapter(PlayerRemoveStaffResult | None)


async def player_remove_staff(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    id_al: int,
) -> PlayerRemoveStaffResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
