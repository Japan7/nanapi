from nanapi.database.discord.message_bulk_delete import (
    MessageBulkDeleteResult,
    message_bulk_delete,
)
from nanapi.database.discord.message_merge import MessageMergeResult, message_merge
from nanapi.models.discord import UpsertMessageBody
from nanapi.utils.clients import get_edgedb
from nanapi.utils.fastapi import NanAPIRouter

router = NanAPIRouter(prefix='/discord', tags=['discord'])


@router.oauth2.put('/messages/{message_id}', response_model=MessageMergeResult)
async def upsert_message(message_id: str, body: UpsertMessageBody):
    """Create or update a Discord message."""
    return await message_merge(get_edgedb(), message_id=message_id, data=body.data)


@router.oauth2.delete('/messages', response_model=list[MessageBulkDeleteResult])
async def delete_messages(message_ids: str):
    """Delete Discord messages."""
    return await message_bulk_delete(get_edgedb(), message_ids=message_ids.split(','))
