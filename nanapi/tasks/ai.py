import asyncio
import logging
import re
from collections.abc import AsyncGenerator
from datetime import datetime

import tiktoken
from gel import AsyncIOClient, AsyncIOExecutor
from pydantic import BaseModel
from tqdm import tqdm

from nanapi.database.discord.message_index_channels_filter_no_page import (
    message_index_channels_filter_no_page,
)
from nanapi.database.discord.message_select_filter_no_page import message_select_filter_no_page
from nanapi.database.discord.page_delete import page_delete
from nanapi.database.discord.page_delete_empty import page_delete_empty
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

MAX_PAGE_SIZE = 50
SPACE_REG = re.compile(r'\s+')
ENCODING = tiktoken.encoding_for_model(AI_EMBEDDING_MODEL_NAME)


class AuthorData(BaseModel):
    username: str
    global_name: str | None


class EmbedFooter(BaseModel):
    text: str


class EmbedField(BaseModel):
    name: str
    value: str


class EmbedData(BaseModel):
    title: str | None = None
    url: str | None = None
    description: str | None = None
    fields: list[EmbedField] | None = None
    footer: EmbedFooter | None = None


class MessageData(BaseModel):
    id: str
    author: AuthorData
    timestamp: datetime
    content: str
    embeds: list[EmbedData]


@webhook_exceptions
async def update_pages(edgedb: AsyncIOClient):
    pages = await page_select_filter_updated_messages(edgedb)
    logger.debug(f'updating {len(pages)} pages')
    for page in tqdm(pages):
        messages_data = [
            MessageData.model_validate(m.data)
            for m in page.messages
            if not m.deleted_at and not m.noindex
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


@webhook_exceptions
async def delete_empty_pages(edgedb: AsyncIOClient):
    resp = await page_delete_empty(edgedb)
    logger.debug(f'deleted {len(resp)} empty pages')


async def yield_messages(
    edgedb: AsyncIOExecutor,
    channel_id: str,
    last_page: PageSelectLastResult | None = None,
):
    if last_page:
        for m in last_page.messages:
            yield MessageData.model_validate(m.data)
    messages = await message_select_filter_no_page(
        edgedb,
        channel_id=channel_id,
        after=last_page.to_timestamp if last_page else None,
    )
    for m in tqdm(messages, leave=False):
        yield MessageData.model_validate(m.data)


async def yield_pages(messages_data: AsyncGenerator[MessageData]):
    page_messages: list[MessageData] = []
    page_lines: list[str] = []
    page_tokens = 0
    async for message_data in messages_data:
        line = format_message(message_data)
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


def format_message(message_data: MessageData) -> str:
    username = message_data.author.username
    author = f'{gn} ({username})' if (gn := message_data.author.global_name) else username
    parts = [f'{author} at {message_data.timestamp:%Y-%m-%d %H:%M} said:']
    if content := message_data.content.strip():
        parts.append(content)
    for i, embed in enumerate(message_data.embeds):
        embed_str = stringify_embed(embed)
        if embed_str:
            parts.append(f'Embed {i}: {embed_str}')
    return SPACE_REG.sub(' ', ' '.join(parts)).strip() + '\n'


def stringify_embed(embed: EmbedData) -> str:
    parts: list[str] = []
    if embed.title:
        parts.append(f'Title: {embed.title}')
    if embed.url:
        parts.append(f'URL: {embed.url}')
    if embed.description:
        parts.append(f'Description: {embed.description}')
    if embed.fields:
        for field in embed.fields:
            parts.append(f'{field.name}: {field.value}')
    if embed.footer:
        parts.append(f'Footer: {embed.footer.text}')
    return ' '.join(parts)


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
        await delete_empty_pages(edgedb)


if __name__ == '__main__':
    logging.basicConfig(level=LOG_LEVEL)
    asyncio.run(main())
