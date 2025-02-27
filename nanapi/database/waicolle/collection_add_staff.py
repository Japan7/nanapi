from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  id := <uuid>$id,
  id_al := <int32>$id_al,
  staff := (select anilist::Staff filter .id_al = id_al),
  _update := (
    update waicolle::Collection
    filter .id = id
    set {
      items += staff,
    }
  ),
select {
  collection := assert_exists(_update) {
    id,
    name,
  },
  staff := assert_exists(staff) {
    id_al,
    name_user_preferred,
    name_native,
  },
}
"""


class CollectionAddStaffResultStaff(BaseModel):
    id_al: int
    name_user_preferred: str
    name_native: str | None


class CollectionAddStaffResultCollection(BaseModel):
    id: UUID
    name: str


class CollectionAddStaffResult(BaseModel):
    collection: CollectionAddStaffResultCollection
    staff: CollectionAddStaffResultStaff


adapter = TypeAdapter(CollectionAddStaffResult)


async def collection_add_staff(
    executor: AsyncIOExecutor,
    *,
    id: UUID,
    id_al: int,
) -> CollectionAddStaffResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        id=id,
        id_al=id_al,
    )
    return adapter.validate_json(resp, strict=False)
