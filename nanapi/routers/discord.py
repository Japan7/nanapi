from typing import Annotated, Any

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
from nanapi.database.discord.message_word_frequency import message_word_frequency
from nanapi.database.discord.rag_query import rag_query
from nanapi.models.discord import MessagesRagResult, UpdateMessageNoindexBody
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_client_edgedb
from nanapi.utils.user_word_analysis import UserWordAnalysis, analyze_user_words
from nanapi.utils.word_frequency import WordFrequencyAnalysis, analyze_word_frequency

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


@router.oauth2_client.get('/messages/word-frequency', response_model=WordFrequencyAnalysis)
async def get_word_frequency(
    channel_id: str | None = None,
    guild_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    min_occurrences: int = 10,
    min_users: int = 2,
    top_n: int = 100,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """
    Analyze word frequency in messages to find community-specific words.
    
    This endpoint helps identify words that are statistically frequent compared to
    typical usage, which can be useful for finding new trigger words for conditional drops.
    
    Parameters:
    - channel_id: Filter by specific channel
    - guild_id: Filter by specific guild/server
    - start_date: ISO format datetime (e.g., "2024-01-01T00:00:00")
    - end_date: ISO format datetime
    - min_occurrences: Minimum times a word must appear (default: 10)
    - min_users: Minimum unique users who must use the word (default: 2)
    - top_n: Number of top words to return (default: 100)
    """
    from datetime import datetime
    
    # Parse datetime strings if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    messages = await message_word_frequency(
        edgedb,
        channel_id=channel_id,
        guild_id=guild_id,
        start_date=start_dt,
        end_date=end_dt,
    )
    
    return analyze_word_frequency(
        messages,
        min_occurrences=min_occurrences,
        min_users=min_users,
        top_n=top_n,
    )


@router.oauth2_client.get('/messages/user-words/{user_id}', response_model=UserWordAnalysis)
async def get_user_characteristic_words(
    user_id: str,
    channel_id: str | None = None,
    guild_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    min_user_count: int = 5,
    min_ratio: float = 2.0,
    top_n: int = 50,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """
    Analyze words characteristic to a specific user.
    
    This endpoint identifies words that a user says significantly more often
    than the rest of the community, revealing their unique speech patterns
    and "signature words".
    
    Parameters:
    - user_id: Discord user ID to analyze
    - channel_id: Filter by specific channel
    - guild_id: Filter by specific guild/server
    - start_date: ISO format datetime (e.g., "2024-01-01T00:00:00")
    - end_date: ISO format datetime
    - min_user_count: Minimum times the user must use a word (default: 5)
    - min_ratio: Minimum ratio of user_freq/community_freq (default: 2.0)
    - top_n: Number of top words to return (default: 50)
    
    Returns:
    - characteristic_words: Words the user uses much more than others
    - unique_words: Words only (or mostly) this user uses
    - comparison_summary: Vocabulary statistics
    """
    from datetime import datetime
    
    # Parse datetime strings if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    messages = await message_word_frequency(
        edgedb,
        channel_id=channel_id,
        guild_id=guild_id,
        start_date=start_dt,
        end_date=end_dt,
    )
    
    return analyze_user_words(
        messages,
        user_id=user_id,
        min_user_count=min_user_count,
        min_ratio=min_ratio,
        top_n=top_n,
    )
