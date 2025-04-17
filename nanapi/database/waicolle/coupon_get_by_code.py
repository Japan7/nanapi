from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  code := <str>$code,
select waicolle::Coupon {
  code,
  claimed_by: {
    user: {
      discord_id,
    },
  },
}
filter .client = global client and .code = code
"""


class CouponGetByCodeResultClaimedByUser(BaseModel):
    discord_id: str


class CouponGetByCodeResultClaimedBy(BaseModel):
    user: CouponGetByCodeResultClaimedByUser


class CouponGetByCodeResult(BaseModel):
    code: str
    claimed_by: list[CouponGetByCodeResultClaimedBy]


adapter = TypeAdapter(CouponGetByCodeResult | None)


async def coupon_get_by_code(
    executor: AsyncIOExecutor,
    *,
    code: str,
) -> CouponGetByCodeResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        code=code,
    )
    return adapter.validate_json(resp, strict=False)
