import asyncio
import io
import logging
import time
from functools import singledispatch, wraps
from typing import Callable, ParamSpec, TypedDict, TypeVar

import aiohttp
import backoff
from yarl import URL

from nanapi.settings import PRODUCER_TOKEN, PRODUCER_UPLOAD_ENDPOINT
from nanapi.utils.clients import get_session

conn_backoff = backoff.on_exception(
    backoff.expo,
    (aiohttp.ClientConnectorError, aiohttp.ClientConnectionError, aiohttp.ContentTypeError),
    max_time=600,
)


def giveup(exception: Exception) -> bool:
    assert isinstance(exception, aiohttp.ClientResponseError)
    return 400 <= exception.status < 500


response_backoff = backoff.on_exception(
    backoff.expo, aiohttp.ClientResponseError, max_time=600, giveup=giveup
)

timeout_backoff = backoff.on_exception(
    backoff.expo, aiohttp.ServerTimeoutError, max_time=300, max_tries=5
)


default_backoff = timeout_backoff(conn_backoff(response_backoff))


class ProducerResponse(TypedDict):
    url: str


@singledispatch
async def to_producer(file: str | URL | io.IOBase) -> ProducerResponse:
    raise RuntimeError('shouldn’t be here')


@to_producer.register
@default_backoff
async def _(file: str | URL) -> ProducerResponse:
    url = URL(file) if isinstance(file, str) else file

    async with get_session().get(url) as resp:
        filename = url.name
        headers: dict[str, str] = {
            'Authorization': PRODUCER_TOKEN,
            'Expires': '0',
            'Filename': filename,
        }

        async with get_session().post(
            PRODUCER_UPLOAD_ENDPOINT, headers=headers, data=resp.content
        ) as req:
            return await req.json()


async def chunk_iter(file: io.IOBase):
    while chunk := file.read(64 * 1024):
        yield chunk


@to_producer.register
@default_backoff
async def _(file: io.IOBase, filename: str) -> ProducerResponse:
    headers: dict[str, str] = {
        'Authorization': PRODUCER_TOKEN,
        'Expires': '0',
        'Filename': filename,
    }

    async with get_session().post(
        PRODUCER_UPLOAD_ENDPOINT, headers=headers, data=chunk_iter(file)
    ) as req:
        return await req.json()


P = ParamSpec('P')
T = TypeVar('T')


def log_time(func: Callable[P, T]):
    logger = logging.getLogger(func.__module__)

    @wraps(func)
    async def decorated(*args: P.args, **kwargs: P.kwargs):
        begin = time.monotonic()
        ret = func(*args, **kwargs)
        if asyncio.iscoroutine(ret):
            ret = await ret
        end = time.monotonic()
        logger.debug(f'{func.__name__} took {end - begin:.2f}s')
        return ret

    return decorated
