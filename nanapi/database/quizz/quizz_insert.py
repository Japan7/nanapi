from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  channel_id := <str>$channel_id,
  description := <str>$description,
  url := <optional str>$url,
  is_image := <bool>$is_image,
  author_discord_id := <str>$author_discord_id,
  author_discord_username := <str>$author_discord_username,
  author := (
    insert user::User {
      discord_id := author_discord_id,
      discord_username := author_discord_username,
    }
    unless conflict on .discord_id
    else (
      update user::User set {
        discord_username := author_discord_username,
      }
    )
  ),
insert quizz::Quizz {
  client := global client,
  channel_id := channel_id,
  description := description,
  url := url,
  is_image := is_image,
  author := author,
}
"""


class QuizzInsertResult(BaseModel):
    id: UUID


adapter = TypeAdapter(QuizzInsertResult)


async def quizz_insert(
    executor: AsyncIOExecutor,
    *,
    channel_id: str,
    description: str,
    is_image: bool,
    author_discord_id: str,
    author_discord_username: str,
    url: str | None = None,
) -> QuizzInsertResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        channel_id=channel_id,
        description=description,
        is_image=is_image,
        author_discord_id=author_discord_id,
        author_discord_username=author_discord_username,
        url=url,
    )
    return adapter.validate_json(resp, strict=False)
