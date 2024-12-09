from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
update waicolle::Player
filter .client = global client and .user.discord_id = discord_id
set {
  frozen_at := datetime_current(),
}
"""


class PlayerFreezeResult(BaseModel):
    id: UUID


adapter = TypeAdapter(PlayerFreezeResult | None)


async def player_freeze(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
) -> PlayerFreezeResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)