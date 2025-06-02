from typing import Annotated, Any

import gel.ai
import orjson
from fastapi import Body, Depends, HTTPException, status
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
from nanapi.database.discord.message_update_noindex import (
    MessageUpdateNoindexResult,
    message_update_noindex,
)
from nanapi.database.discord.rag_query import RagQueryResultObject, rag_query
from nanapi.models.discord import UpdateMessageNoindexBody
from nanapi.settings import AI_EMBEDDING_MODEL_NAME
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_client_edgedb

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


@router.oauth2_client.get('/messages/rag', response_model=list[RagQueryResultObject])
async def rag(search_query: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Retrieve relevant chat sections based on a search query in French."""
    rag = await gel.ai.create_async_rag_client(edgedb, model='')  # pyright: ignore[reportUnknownMemberType]
    embeddings = await rag.generate_embeddings(search_query, model=AI_EMBEDDING_MODEL_NAME)
    resp = await rag_query(edgedb, embeddings=embeddings[:2000])
    objects: list[RagQueryResultObject] = []
    for result in resp:
        result.object.messages.sort(key=lambda m: m.timestamp)
        objects.append(result.object)
    return objects


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
    '/messages/{message_id}/noindex',
    response_model=MessageUpdateNoindexResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def update_message_noindex(
    message_id: str,
    body: UpdateMessageNoindexBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Update indexation instructions of a Discord message."""
    resp = await message_update_noindex(edgedb, message_id=message_id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp
