from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  key := <str>$key,
select redis::Data {
  key,
  value,
}
filter .key = key
"""


class DataGetByKeyResult(BaseModel):
    key: str
    value: str


adapter = TypeAdapter(DataGetByKeyResult | None)


async def data_get_by_key(
    executor: AsyncIOExecutor,
    *,
    key: str,
) -> DataGetByKeyResult | None:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
        key=key,
    )
    return adapter.validate_json(resp, strict=False)
