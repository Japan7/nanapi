from typing import Annotated, Any

from fastapi import Body, Depends
from gel import AsyncIOClient
from pydantic import Json

from nanapi.database.discord.message_bulk_delete import (
    MessageBulkDeleteResult,
    message_bulk_delete,
)
from nanapi.database.discord.message_merge import MessageMergeResult, message_merge
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/discord', tags=['discord'])


@router.oauth2_client_restricted.delete('/messages', response_model=list[MessageBulkDeleteResult])
async def delete_messages(message_ids: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete Discord messages."""
    return await message_bulk_delete(edgedb, message_ids=message_ids.split(','))


@router.oauth2_client_restricted.put('/messages/{message_id}', response_model=MessageMergeResult)
async def upsert_message(
    message_id: str,
    data: Annotated[Json[Any], Body()],
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Create or update a Discord message."""
    return await message_merge(edgedb, message_id=message_id, data=data)
