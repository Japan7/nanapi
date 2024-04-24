from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
select pot::Pot { amount, count }
filter .client = global client and .user.discord_id = discord_id
"""


class PotGetByUserResult(BaseModel):
    amount: float
    count: int


adapter = TypeAdapter(PotGetByUserResult | None)


async def pot_get_by_user(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
) -> PotGetByUserResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
    )
    return adapter.validate_json(resp, strict=False)
