from datetime import datetime

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  discord_id := <int64>$discord_id,
  discord_username := <str>$discord_username,
  birthday := <optional datetime>$birthday,
  full_name := <optional str>$full_name,
  graduation_year := <optional int16>$graduation_year,
  photo := <optional str>$photo,
  pronouns := <optional str>$pronouns,
  n7_major := <optional str>$n7_major,
  telephone := <optional str>$telephone,
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
  profile := (
    insert user::Profile {
      birthday := birthday,
      full_name := full_name,
      graduation_year := graduation_year,
      photo := photo,
      pronouns := pronouns,
      n7_major := n7_major,
      telephone := telephone,
      user := user,
    }
    unless conflict on .user
    else (
      update user::Profile set {
        birthday := birthday,
        full_name := full_name,
        graduation_year := graduation_year,
        photo := photo,
        pronouns := pronouns,
        n7_major := n7_major,
        telephone := telephone,
      }
    )
  )
select profile {
  birthday,
  graduation_year,
  full_name,
  photo,
  pronouns,
  n7_major,
  telephone,
  user: {
    discord_id,
    discord_id_str,
  },
}
"""


class ProfileMergeSelectResultUser(BaseModel):
    discord_id: int
    discord_id_str: str


class ProfileMergeSelectResult(BaseModel):
    birthday: datetime | None
    graduation_year: int | None
    full_name: str | None
    photo: str | None
    pronouns: str | None
    n7_major: str | None
    telephone: str | None
    user: ProfileMergeSelectResultUser


adapter = TypeAdapter(ProfileMergeSelectResult)


async def profile_merge_select(
    executor: AsyncIOExecutor,
    *,
    discord_id: int,
    discord_username: str,
    birthday: datetime | None = None,
    full_name: str | None = None,
    graduation_year: int | None = None,
    photo: str | None = None,
    pronouns: str | None = None,
    n7_major: str | None = None,
    telephone: str | None = None,
) -> ProfileMergeSelectResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        discord_id=discord_id,
        discord_username=discord_username,
        birthday=birthday,
        full_name=full_name,
        graduation_year=graduation_year,
        photo=photo,
        pronouns=pronouns,
        n7_major=n7_major,
        telephone=telephone,
    )
    return adapter.validate_json(resp, strict=False)
