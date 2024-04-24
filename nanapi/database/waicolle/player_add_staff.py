from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  id_al := <int32>$id_al,
  staff := (select anilist::Staff filter .id_al = id_al),
  _update := (
    update waicolle::Player
    filter .client = global client and .user.discord_id = discord_id
    set {
      tracked_items += staff,
    }
  )
select {
  player := assert_exists(_update),
  staff := assert_exists(staff) {
    id_al,
    name_user_preferred,
    name_native,
  },
}
"""


class PlayerAddStaffResultStaff(BaseModel):
    id_al: int
    name_user_preferred: str
    name_native: str | None


class PlayerAddStaffResultPlayer(BaseModel):
    id: UUID


class PlayerAddStaffResult(BaseModel):
    player: PlayerAddStaffResultPlayer
    staff: PlayerAddStaffResultStaff


adapter = TypeAdapter(PlayerAddStaffResult)


async def player_add_staff(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    id_al: int,
) -> PlayerAddStaffResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
