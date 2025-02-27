from datetime import datetime

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  pattern := <str>$pattern
select user::Profile {
  birthday,
  full_name,
  graduation_year,
  photo,
  pronouns,
  n7_major,
  telephone,
  user: {
    discord_id,
    discord_id_str,
  },
}
filter (
  (.full_name ilike pattern) ?? false
  or (.n7_major ilike pattern) ?? false
  or (.pronouns ilike pattern) ?? false
)
"""


class ProfileSelectIlikeResultUser(BaseModel):
    discord_id: int
    discord_id_str: str


class ProfileSelectIlikeResult(BaseModel):
    birthday: datetime | None
    full_name: str | None
    graduation_year: int | None
    photo: str | None
    pronouns: str | None
    n7_major: str | None
    telephone: str | None
    user: ProfileSelectIlikeResultUser


adapter = TypeAdapter(list[ProfileSelectIlikeResult])


async def profile_select_ilike(
    executor: AsyncIOExecutor,
    *,
    pattern: str,
) -> list[ProfileSelectIlikeResult]:
    resp = await executor.query_json(
        EDGEQL_QUERY,
        pattern=pattern,
    )
    return adapter.validate_json(resp, strict=False)
