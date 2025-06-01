import asyncio
import logging
import re
from collections.abc import AsyncGenerator
from datetime import datetime
from itertools import count

import tiktoken
from gel import AsyncIOClient, AsyncIOExecutor
from pydantic import BaseModel
from tqdm import tqdm

from nanapi.database.discord.message_index_channels_filter_no_page import (
    message_index_channels_filter_no_page,
)
from nanapi.database.discord.message_select_filter_no_page import message_select_filter_no_page
from nanapi.database.discord.page_delete import page_delete
from nanapi.database.discord.page_insert import page_insert
from nanapi.database.discord.page_select_filter_updated_messages import (
    page_select_filter_updated_messages,
)
from nanapi.database.discord.page_select_last import PageSelectLastResult, page_select_last
from nanapi.database.discord.page_update import page_update
from nanapi.settings import (
    AI_EMBEDDING_MODEL_MAX_TOKENS,
    AI_EMBEDDING_MODEL_NAME,
    AI_MESSAGEPAGES_FOR_CLIENTS,
    LOG_LEVEL,
)
from nanapi.utils.fastapi import get_client_edgedb
from nanapi.utils.logs import webhook_exceptions

logger = logging.getLogger(__name__)

YIELD_LIMIT = 100000
MAX_PAGE_SIZE = 100
SPACE_REG = re.compile(r'\s+')
ENCODING = tiktoken.encoding_for_model(AI_EMBEDDING_MODEL_NAME)


class AuthorData(BaseModel):
    username: str
    global_name: str | None
    bot: bool | None = None


class MessageData(BaseModel):
    id: str
    channel_id: str
    content: str
    timestamp: datetime
    author: AuthorData


@webhook_exceptions
async def update_pages(edgedb: AsyncIOClient):
    pages = await page_select_filter_updated_messages(edgedb)
    logger.debug(f'updating {len(pages)} pages')
    for page in tqdm(pages):
        messages_data = [
            MessageData.model_validate(m.data) for m in page.messages if not m.deleted_at
        ]
        messages_data.sort(key=lambda m: m.timestamp)
        context = ''.join(filter(None, map(format_message, messages_data)))
        await page_update(
            edgedb, id=page.id, context=context, message_ids=[m.id for m in messages_data]
        )


@webhook_exceptions
async def insert_pages(edgedb: AsyncIOClient):
    channel_ids = await message_index_channels_filter_no_page(edgedb)
    logger.debug(f'creating pages in {len(channel_ids)} channels')
    pbar = tqdm(channel_ids)
    for channel_id in pbar:
        pbar.set_description(channel_id)
        last_page = await page_select_last(edgedb, channel_id=channel_id)
        async for tx in edgedb.transaction():
            async with tx:
                async for page_messages, context in yield_pages(
                    yield_messages(tx, channel_id, last_page)
                ):
                    await page_insert(
                        tx,
                        context=context,
                        channel_id=channel_id,
                        message_ids=[m.id for m in page_messages],
                    )
                if last_page:
                    await page_delete(tx, id=last_page.id)


async def yield_messages(
    edgedb: AsyncIOExecutor,
    channel_id: str,
    last_page: PageSelectLastResult | None = None,
):
    if last_page:
        for m in last_page.messages:
            yield MessageData.model_validate(m.data)
    for i in count():
        offset = i * YIELD_LIMIT
        logger.debug(f'fetching {YIELD_LIMIT} messages for {channel_id} with {offset=}')
        messages = await message_select_filter_no_page(
            edgedb,
            channel_id=channel_id,
            offset=offset,
            limit=YIELD_LIMIT,
        )
        logger.debug(f'fetched {len(messages)} messages for {channel_id}')
        for m in messages:
            yield MessageData.model_validate(m.data)
        if len(messages) < YIELD_LIMIT:
            break


async def yield_pages(messages_data: AsyncGenerator[MessageData]):
    page_messages: list[MessageData] = []
    page_lines: list[str] = []
    page_tokens = 0
    async for message_data in messages_data:
        line = format_message(message_data)
        if not line:
            continue
        line_tokens = len(ENCODING.encode(line))
        if line_tokens > AI_EMBEDDING_MODEL_MAX_TOKENS:
            if page_lines:
                yield page_messages, ''.join(page_lines)
                page_messages, page_lines, page_tokens = overlap(page_messages, page_lines)
            yield [message_data], line
            continue
        if (
            len(page_messages) == MAX_PAGE_SIZE
            or page_tokens + line_tokens > AI_EMBEDDING_MODEL_MAX_TOKENS
        ):
            yield page_messages, ''.join(page_lines)
            page_messages, page_lines, page_tokens = overlap(page_messages, page_lines)
        page_messages.append(message_data)
        page_lines.append(line)
        page_tokens += line_tokens
    if page_lines:
        yield page_messages, ''.join(page_lines)


def format_message(message_data: MessageData) -> str | None:
    if message_data.author.bot:
        return
    username = message_data.author.username
    author = f'{gn} ({username})' if (gn := message_data.author.global_name) else username
    content = SPACE_REG.sub(' ', message_data.content).strip()
    if content:
        return (
            f'Author: {author}; '
            f'Timestamp: {message_data.timestamp:%Y-%m-%d %H:%M:%S}; '
            f'Content: {content}\n'
        )


def overlap(lines_messages: list[MessageData], lines: list[str]):
    assert len(lines_messages) == len(lines)
    messages_overlap = lines_messages[int(len(lines_messages) * 0.8) :]
    lines_overlap = lines[int(len(lines) * 0.8) :]
    return messages_overlap, lines_overlap, len(ENCODING.encode(''.join(lines_overlap)))


async def main():
    for client_id in AI_MESSAGEPAGES_FOR_CLIENTS:
        edgedb = get_client_edgedb(client_id)
        await update_pages(edgedb)
        await insert_pages(edgedb)


if __name__ == '__main__':
    logging.basicConfig(level=LOG_LEVEL)
    asyncio.run(main())
