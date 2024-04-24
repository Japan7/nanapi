from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  custom_image := <optional str>$custom_image,
  custom_name := <optional str>$custom_name,
update waicolle::Waifu
filter .id = id
set {
  custom_image := (
    (<str>{} if custom_image ilike '' else custom_image)
    if exists custom_image
    else .custom_image
  ),
  custom_name := (
    (<str>{} if custom_name ilike '' else custom_name)
    if exists custom_name
    else .custom_name
  ),
}
"""


class WaifuUpdateCustomImageNameResult(BaseModel):
    id: UUID


adapter = TypeAdapter(WaifuUpdateCustomImageNameResult | None)


async def waifu_update_custom_image_name(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    custom_image: str | None = None,
    custom_name: str | None = None,
) -> WaifuUpdateCustomImageNameResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        custom_image=custom_image,
        custom_name=custom_name,
    )
    return adapter.validate_json(resp, strict=False)
