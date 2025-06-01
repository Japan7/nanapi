from typing import Annotated, Any

import gel.ai
import orjson
from fastapi import Body, Depends
from gel import AsyncIOClient
from pydantic import Json

from nanapi.database.discord.message_bulk_delete import (
    MessageBulkDeleteResult,
    message_bulk_delete,
)
from nanapi.database.discord.message_bulk_insert import (
    MessageBulkInsertResult,
    message_bulk_insert,
)
from nanapi.database.discord.message_merge import MessageMergeResult, message_merge
from nanapi.database.discord.rag_query import RagQueryResultObjectMessages, rag_query
from nanapi.settings import AI_EMBEDDING_MODEL_NAME
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb

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


@router.oauth2_client.get('/messages/rag', response_model=list[list[RagQueryResultObjectMessages]])
async def rag(search_query: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Retrieve relevant chat sections based on a search query in French."""
    rag = await gel.ai.create_async_rag_client(edgedb, model='')  # pyright: ignore[reportUnknownMemberType]
    embeddings = await rag.generate_embeddings(search_query, model=AI_EMBEDDING_MODEL_NAME)
    resp = await rag_query(edgedb, embeddings=embeddings[:2000])
    return [r.object.messages for r in resp]


@router.oauth2_client_restricted.put('/messages/{message_id}', response_model=MessageMergeResult)
async def upsert_message(
    message_id: str,
    data: Annotated[Json[Any], Body()],
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Create or update a Discord message."""
    return await message_merge(edgedb, message_id=message_id, data=data)
