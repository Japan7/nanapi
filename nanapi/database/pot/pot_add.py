from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <str>$discord_id,
  discord_username := <str>$discord_username,
  amount := <float32>$amount,
  user := (
    insert user::User {
      discord_id := discord_id,
      discord_username := discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := discord_username,
      }
    )
  ),
  pot := (
    insert pot::Pot {
      client := global client,
      amount := amount,
      count := 1,
      user := user,
    }
    unless conflict on ((.client, .user))
    else (
      update pot::Pot set {
        amount := .amount + amount,
        count := .count + 1,
      }
    )
  ),
select pot { amount, count }
"""


class PotAddResult(BaseModel):
    amount: float
    count: int


adapter = TypeAdapter(PotAddResult | None)


async def pot_add(
    executor: AsyncIOExecutor,
    *,
    discord_id: str,
    discord_username: str,
    amount: float,
) -> PotAddResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        discord_username=discord_username,
        amount=amount,
    )
    return adapter.validate_json(resp, strict=False)
