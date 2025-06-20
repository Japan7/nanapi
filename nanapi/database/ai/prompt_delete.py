# Generated by gel-pydantic-codegen
# pyright: strict
from uuid import UUID

from gel import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
delete ai::Prompt filter .client = global client and .name = <str>$name
"""


class PromptDeleteResult(BaseModel):
    id: UUID


adapter = TypeAdapter[PromptDeleteResult | None](PromptDeleteResult | None)


async def prompt_delete(
    executor: AsyncIOExecutor,
    *,
    name: str,
) -> PromptDeleteResult | None:
    resp = await executor.query_single_json(  # pyright: ignore[reportUnknownMemberType]
        EDGEQL_QUERY,
        name=name,
    )
    return adapter.validate_json(resp, strict=False)
