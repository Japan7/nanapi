from fastapi import Depends
from gel import AsyncIOClient

from nanapi.database.discord.message_bulk_delete import (
    MessageBulkDeleteResult,
    message_bulk_delete,
)
from nanapi.database.discord.message_merge import MessageMergeResult, message_merge
from nanapi.models.discord import UpsertMessageBody
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/discord', tags=['discord'])


@router.oauth2_client_restricted.put('/messages/{message_id}', response_model=MessageMergeResult)
async def upsert_message(
    message_id: str,
    body: UpsertMessageBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Create or update a Discord message."""
    return await message_merge(edgedb, message_id=message_id, data=body.data)


@router.oauth2_client_restricted.delete('/messages', response_model=list[MessageBulkDeleteResult])
async def delete_messages(message_ids: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete Discord messages."""
    return await message_bulk_delete(edgedb, message_ids=message_ids.split(','))
