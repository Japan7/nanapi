import argparse
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, cast
from urllib.parse import quote
from uuid import UUID

import aiohttp
import orjson
from gel import AsyncIOClient
from pydantic import BaseModel
from tqdm import tqdm

from nanapi.database.discord.message_bulk_insert import message_bulk_insert
from nanapi.database.discord.message_bulk_update_noindex import message_bulk_update_noindex
from nanapi.database.discord.reaction_bulk_delete_by_message_ids import (
    reaction_bulk_delete_by_message_ids,
)
from nanapi.settings import (
    DISCORD_BOT_TOKEN,
    DISCORD_SYNC_BATCH_SIZE,
    DISCORD_SYNC_CONCURRENCY,
    DISCORD_SYNC_LOOKBACK_HOURS,
    LOG_LEVEL,
)
from nanapi.utils.fastapi import get_client_edgedb
from nanapi.utils.logs import webhook_exceptions

logger = logging.getLogger(__name__)

DISCORD_API_BASE_URL = 'https://discord.com/api/v10'
CHANNEL_TYPE_GUILD_TEXT = 0
MESSAGE_FLAG_EPHEMERAL = 1 << 6
NANACHAN_THREAD_NOINDEX_AFTER = datetime(2024, 4, 15, tzinfo=timezone.utc)


def as_dict_list(payload: Any) -> list[dict[str, Any]]:
    assert isinstance(payload, list)
    return cast(list[dict[str, Any]], payload)


@dataclass
class Args:
    guild_id: str = ''
    client_id: UUID | None = None
    nanachan_user_id: str = ''


class ThreadMetadata(BaseModel):
    create_timestamp: datetime | None = None


class ChannelData(BaseModel):
    id: str
    type: int
    name: str | None = None
    owner_id: str | None = None
    thread_metadata: ThreadMetadata | None = None


class AuthorData(BaseModel):
    id: str
    bot: bool | None = None


class EmojiData(BaseModel):
    name: str | None = None
    id: str | None = None
    animated: bool | None = None


class CountDetails(BaseModel):
    burst: int = 0


class ReactionData(BaseModel):
    emoji: EmojiData
    count_details: CountDetails | None = None


class MessageData(BaseModel):
    id: str
    channel_id: str
    author: AuthorData
    timestamp: datetime
    flags: int | None = None
    reactions: list[ReactionData] | None = None


class ActiveThreadsResponse(BaseModel):
    threads: list[ChannelData]


class DiscordClient:
    def __init__(self, token: str, concurrency: int) -> None:
        self._headers = {
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json',
        }
        self._semaphore = asyncio.Semaphore(max(1, concurrency))
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=None, connect=30, sock_connect=30, sock_read=60)
        self._session = aiohttp.ClientSession(headers=self._headers, timeout=timeout)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._session is not None:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        assert self._session is not None
        return self._session

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> Any:
        url = f'{DISCORD_API_BASE_URL}{path}'
        attempt = 0
        while True:
            attempt += 1
            async with (
                self._semaphore,
                self.session.request(method, url, params=params) as response,
            ):
                if response.status == 429:
                    payload = await response.json(content_type=None)
                    retry_after = float(payload.get('retry_after', 1))
                    logger.warning(f'rate limited on {path}, retrying in {retry_after:.2f}s')
                elif response.status >= 500 and attempt < 6:
                    retry_after = min(2**attempt, 30)
                    logger.warning(
                        f'Discord API error {response.status} on {path}, '
                        f'retrying in {retry_after}s'
                    )
                else:
                    response.raise_for_status()
                    return await response.json(loads=orjson.loads)
            await asyncio.sleep(retry_after)

    async def list_guild_channels(self, guild_id: str) -> list[ChannelData]:
        payload = await self.request_json('GET', f'/guilds/{guild_id}/channels')
        return [ChannelData.model_validate(item) for item in payload]

    async def list_active_threads(self, guild_id: str) -> list[ChannelData]:
        payload = await self.request_json('GET', f'/guilds/{guild_id}/threads/active')
        return ActiveThreadsResponse.model_validate(payload).threads

    async def list_archived_threads(self, channel_id: str) -> list[ChannelData]:
        before: str | None = None
        threads: list[ChannelData] = []
        while True:
            params = {'limit': '100'}
            if before is not None:
                params['before'] = before
            payload = await self.request_json(
                'GET', f'/channels/{channel_id}/threads/archived/public', params=params
            )
            page_threads = [
                ChannelData.model_validate(item) for item in payload.get('threads', [])
            ]
            threads.extend(page_threads)
            if not payload.get('has_more') or not page_threads:
                return threads
            last_timestamp = page_threads[-1].thread_metadata
            if last_timestamp is None or last_timestamp.create_timestamp is None:
                return threads
            before = last_timestamp.create_timestamp.isoformat()

    async def list_channel_messages(
        self, channel_id: str, *, before: str | None = None
    ) -> list[dict[str, Any]]:
        params = {'limit': '100'}
        if before is not None:
            params['before'] = before
        payload = await self.request_json('GET', f'/channels/{channel_id}/messages', params=params)
        return as_dict_list(payload)

    async def list_reaction_users(
        self,
        channel_id: str,
        message_id: str,
        emoji: EmojiData,
    ) -> list[dict[str, Any]]:
        if emoji.name is None:
            return []
        emoji_key = f'{emoji.name}:{emoji.id}' if emoji.id else emoji.name
        emoji_path = quote(emoji_key, safe='')
        after: str | None = None
        users: list[dict[str, Any]] = []
        while True:
            params = {'limit': '100'}
            if after is not None:
                params['after'] = after
            payload = await self.request_json(
                'GET',
                f'/channels/{channel_id}/messages/{message_id}/reactions/{emoji_path}',
                params=params,
            )
            page_users = as_dict_list(payload)
            users.extend(page_users)
            if len(page_users) < 100:
                return users
            last_user = page_users[-1].get('id')
            if not isinstance(last_user, str):
                return users
            after = last_user


def parse_args() -> Args:
    parser = argparse.ArgumentParser('discord_sync')
    _ = parser.add_argument('--guild-id', required=True)
    _ = parser.add_argument('--client-id', required=True, type=UUID)
    _ = parser.add_argument('--nanachan-user-id', required=True)
    args = Args()
    _ = parser.parse_args(namespace=args)
    assert args.client_id is not None
    return args


def is_ephemeral(message: MessageData) -> bool:
    return bool(message.flags and message.flags & MESSAGE_FLAG_EPHEMERAL)


def is_nanachan_thread(channel: ChannelData, nanachan_user_id: str) -> bool:
    if channel.owner_id != nanachan_user_id:
        return False
    if channel.thread_metadata is None or channel.thread_metadata.create_timestamp is None:
        return False
    return channel.thread_metadata.create_timestamp > NANACHAN_THREAD_NOINDEX_AFTER


def build_noindex(
    message: MessageData,
    *,
    nanachan_thread_ids: set[str],
    nanachan_user_id: str,
) -> str:
    if message.author.id == nanachan_user_id:
        return 'nanachan'
    if message.author.bot:
        return 'bot'
    if message.channel_id in nanachan_thread_ids:
        return 'nanachan thread'
    return ''


async def fetch_message_reactions(
    discord: DiscordClient, message_payload: dict[str, Any]
) -> list[dict[str, Any]]:
    message = MessageData.model_validate(message_payload)
    reactions: list[dict[str, Any]] = []
    for reaction_payload in message_payload.get('reactions', []):
        reaction = ReactionData.model_validate(reaction_payload)
        try:
            users = await discord.list_reaction_users(
                message.channel_id, message.id, reaction.emoji
            )
        except Exception:
            logger.exception(f'failed to fetch reactions for message {message.id}')
            continue
        reactions.append({'reaction': reaction_payload, 'users': users})
    return reactions


async def flush_batch(
    edgedb: AsyncIOClient,
    *,
    batch_messages: list[dict[str, Any]],
    batch_noindexes: list[dict[str, str]],
) -> None:
    if not batch_messages:
        return
    message_ids = [payload['message']['id'] for payload in batch_messages]
    serialized_messages = [orjson.dumps(payload).decode() for payload in batch_messages]
    serialized_noindexes = [orjson.dumps(payload).decode() for payload in batch_noindexes]
    async for tx in edgedb.transaction():
        async with tx:
            await reaction_bulk_delete_by_message_ids(tx, message_ids=message_ids)
            await message_bulk_insert(tx, messages=serialized_messages)
            await message_bulk_update_noindex(tx, items=serialized_noindexes)
            return


async def sync_channel(
    discord: DiscordClient,
    edgedb: AsyncIOClient,
    *,
    guild_id: str,
    channel: ChannelData,
    cutoff: datetime | None,
    nanachan_thread_ids: set[str],
    nanachan_user_id: str,
    batch_size: int,
) -> int:
    before: str | None = None
    inserted = 0
    batch_messages: list[dict[str, Any]] = []
    batch_noindexes: list[dict[str, str]] = []
    while True:
        page = await discord.list_channel_messages(channel.id, before=before)
        if not page:
            break
        before = page[-1]['id']
        reached_cutoff = False
        for message_payload in page:
            message = MessageData.model_validate(message_payload)
            if cutoff is not None and message.timestamp < cutoff:
                reached_cutoff = True
                break
            if is_ephemeral(message):
                continue
            message_payload['guild_id'] = guild_id
            reactions = await fetch_message_reactions(discord, message_payload)
            batch_messages.append({'message': message_payload, 'reactions': reactions})
            batch_noindexes.append(
                {
                    'message_id': message.id,
                    'noindex': build_noindex(
                        message,
                        nanachan_thread_ids=nanachan_thread_ids,
                        nanachan_user_id=nanachan_user_id,
                    ),
                }
            )
            if len(batch_messages) >= batch_size:
                await flush_batch(
                    edgedb,
                    batch_messages=batch_messages,
                    batch_noindexes=batch_noindexes,
                )
                inserted += len(batch_messages)
                batch_messages = []
                batch_noindexes = []
        if reached_cutoff:
            break
    if batch_messages:
        await flush_batch(edgedb, batch_messages=batch_messages, batch_noindexes=batch_noindexes)
        inserted += len(batch_messages)
    if inserted:
        logger.info(f'finished channel {channel.id} with {inserted} messages processed')
    return inserted


async def discover_channels(
    discord: DiscordClient,
    *,
    guild_id: str,
    nanachan_user_id: str,
) -> tuple[list[ChannelData], set[str]]:
    guild_channels = await discord.list_guild_channels(guild_id)
    text_channels = [
        channel for channel in guild_channels if channel.type == CHANNEL_TYPE_GUILD_TEXT
    ]
    threads_by_id: dict[str, ChannelData] = {}
    pbar = tqdm(text_channels, desc='discovering archived threads', unit='channel')
    for channel in pbar:
        pbar.set_postfix_str(channel.name or channel.id)
        for thread in await discord.list_archived_threads(channel.id):
            threads_by_id[thread.id] = thread
    for thread in await discord.list_active_threads(guild_id):
        threads_by_id[thread.id] = thread
    nanachan_thread_ids = {
        thread.id
        for thread in threads_by_id.values()
        if is_nanachan_thread(thread, nanachan_user_id)
    }
    channels = [*text_channels, *threads_by_id.values()]
    logger.info(
        f'discovered {len(text_channels)} text channels and {len(threads_by_id)} threads to sync'
    )
    return channels, nanachan_thread_ids


@webhook_exceptions
async def sync_discord(args: Args) -> None:
    if not DISCORD_BOT_TOKEN:
        raise ValueError('DISCORD_BOT_TOKEN must be set in local settings')
    assert args.client_id is not None
    edgedb = get_client_edgedb(args.client_id)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=DISCORD_SYNC_LOOKBACK_HOURS)
    logger.info(f'syncing from {cutoff.isoformat()}')
    async with DiscordClient(DISCORD_BOT_TOKEN, DISCORD_SYNC_CONCURRENCY) as discord:
        channels, nanachan_thread_ids = await discover_channels(
            discord, guild_id=args.guild_id, nanachan_user_id=args.nanachan_user_id
        )
        channel_semaphore = asyncio.Semaphore(max(1, DISCORD_SYNC_CONCURRENCY))

        async def sync_with_limit(channel: ChannelData) -> int:
            async with channel_semaphore:
                return await sync_channel(
                    discord,
                    edgedb,
                    guild_id=args.guild_id,
                    channel=channel,
                    cutoff=cutoff,
                    nanachan_thread_ids=nanachan_thread_ids,
                    nanachan_user_id=args.nanachan_user_id,
                    batch_size=max(1, DISCORD_SYNC_BATCH_SIZE),
                )

        tasks = [asyncio.create_task(sync_with_limit(channel)) for channel in channels]
        processed_counts: list[int] = []
        pbar = tqdm(total=len(tasks), desc='syncing channels', unit='channel')
        for task in asyncio.as_completed(tasks):
            processed_counts.append(await task)
            pbar.update()
        pbar.close()
        logger.info(f'processed {sum(processed_counts)} messages across {len(channels)} channels')


async def main() -> None:
    args = parse_args()
    await sync_discord(args)


if __name__ == '__main__':
    logging.basicConfig(level=LOG_LEVEL)
    asyncio.run(main())
