from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  title := <str>$title,
  _external := (
    insert projection::ExternalMedia {
      client := global client,
      title := title
    }
  )
update projection::Projection
filter .id = id
set { external_medias += _external }
"""


class ProjoAddExternalMediaResult(BaseModel):
    id: UUID


adapter = TypeAdapter(ProjoAddExternalMediaResult | None)


async def projo_add_external_media(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    title: str,
) -> ProjoAddExternalMediaResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        title=title,
    )
    return adapter.validate_json(resp, strict=False)
