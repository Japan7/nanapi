from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  code := <str>$code,
delete waicolle::Coupon
filter .client = global client and .code = code
"""


class CouponDeleteResult(BaseModel):
    id: UUID


adapter = TypeAdapter(CouponDeleteResult | None)


async def coupon_delete(
    executor: AsyncIOExecutor,
    *,
    code: str,
) -> CouponDeleteResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        code=code,
    )
    return adapter.validate_json(resp, strict=False)
