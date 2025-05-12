from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  id_al := <int32>$id_al,
  media := (select anilist::Media filter .id_al = id_al),
update waicolle::Player
filter .client = global client and .user.discord_id = discord_id
set {
  tracked_items -= media,
}
"""


class PlayerRemoveMediaResult(BaseModel):
    id: UUID


adapter = TypeAdapter(PlayerRemoveMediaResult | None)


async def player_remove_media(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    id_al: int,
) -> PlayerRemoveMediaResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
