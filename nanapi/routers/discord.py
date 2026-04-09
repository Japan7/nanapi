import logging
from typing import Annotated, Any

import orjson
from fastapi import Body, Depends, HTTPException, status
from gel import AsyncIOClient
from pydantic import BaseModel, Json

from nanapi.database.discord.message_bulk_delete import (
    MessageBulkDeleteResult,
    message_bulk_delete,
)
from nanapi.database.discord.message_bulk_insert import (
    MessageBulkInsertResult,
    message_bulk_insert,
)
from nanapi.database.discord.message_bulk_update_noindex import (
    MessageBulkUpdateNoindexResult,
    message_bulk_update_noindex,
)
from nanapi.database.discord.message_merge import MessageMergeResult, message_merge
from nanapi.database.discord.rag_query import rag_query
from nanapi.models.discord import (
    BulkUpdateMessageNoindexBodyItem,
    MessagesRagResult,
)
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_client_edgedb

logger = logging.getLogger(__name__)


class Emoji(BaseModel):
    name: str
    emoji_id: str | None = None


def parse_emoji(emoji: str):
    parts = emoji.split(':')
    if len(parts) > 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    name = parts[0]
    emoji_id = parts[1] if len(parts) == 2 else None
    return Emoji(name=name, emoji_id=emoji_id)


router = NanAPIRouter(prefix='/discord', tags=['discord'])


@router.oauth2_client_restricted.post('/messages', response_model=list[MessageBulkInsertResult])
async def bulk_insert_messages(
    messages: Annotated[list[Json[Any]], Body()],
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Bulk create Discord messages."""
    return await message_bulk_insert(
        edgedb,
        messages=[orjson.dumps(data).decode() for data in messages],
    )


@router.oauth2_client_restricted.delete('/messages', response_model=list[MessageBulkDeleteResult])
async def delete_messages(message_ids: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete Discord messages."""
    return await message_bulk_delete(edgedb, message_ids=message_ids.split(','))


@router.oauth2_client.get('/messages/rag', response_model=list[MessagesRagResult])
async def messages_rag(
    search_query: str,
    limit: int = 50,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Retrieve relevant chat sections based on a search query in French."""
    resp = await rag_query(edgedb, search_query=search_query, limit=limit)
    return [MessagesRagResult(object=result.object, distance=result.distance) for result in resp]


@router.oauth2_client_restricted.put(
    '/messages/{message_id}',
    response_model=MessageMergeResult,
    responses={status.HTTP_400_BAD_REQUEST: dict(model=HTTPExceptionModel)},
)
async def upsert_message(
    message_id: str,
    data: Annotated[Json[Any], Body()],
    noindex: str | None = None,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Create or update a Discord message."""
    if data['id'] != message_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return await message_merge(edgedb, message_id=message_id, data=data, noindex=noindex)


@router.oauth2_client_restricted.put(
    '/noindex',
    response_model=list[MessageBulkUpdateNoindexResult],
)
async def bulk_update_message_noindex(
    body: list[BulkUpdateMessageNoindexBodyItem],
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Update indexation instructions for multiple Discord messages."""
    return await message_bulk_update_noindex(
        edgedb, items=[orjson.dumps(item.model_dump()).decode() for item in body]
    )
