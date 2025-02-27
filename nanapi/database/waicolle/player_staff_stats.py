from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
  id_al := <int32>$id_al,
  staff := (select anilist::Staff filter .id_al = id_al),
  charas := (
    select staff.character_edges.character
    filter (.image_large not ilike '%/default.jpg')
  ),
  nb_charas := count(charas),
  owned := (
    select waicolle::Waifu
    filter .client = global client
    and .owner = assert_exists(player)
    and .character in charas
    and not .disabled
  ),
  owned_ids := (select owned.character.id_al),
  nb_owned := count(owned_ids),
select {
  staff := assert_exists(staff) {
    id_al,
    name_user_preferred,
    name_native,
  },
  nb_charas := nb_charas,
  nb_owned := nb_owned,
}
"""


class PlayerStaffStatsResultStaff(BaseModel):
    id_al: int
    name_user_preferred: str
    name_native: str | None


class PlayerStaffStatsResult(BaseModel):
    staff: PlayerStaffStatsResultStaff
    nb_charas: int
    nb_owned: int


adapter = TypeAdapter(PlayerStaffStatsResult)


async def player_staff_stats(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    id_al: int,
) -> PlayerStaffStatsResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
