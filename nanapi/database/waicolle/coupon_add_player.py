from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  code := <str>$code,
  discord_id := <int64>$discord_id,
  player := (select waicolle::Player filter .client = global client and .user.discord_id = discord_id),
update waicolle::Coupon
filter .client = global client and .code = code
set {
  claimed_by += player,
}
"""


class CouponAddPlayerResult(BaseModel):
    id: UUID


adapter = TypeAdapter(CouponAddPlayerResult | None)


async def coupon_add_player(
    executor: AsyncIOExecutor,
    *,
    code: str,
    discord_id: int,
) -> CouponAddPlayerResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        code=code,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
