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
    (aiohttp.ClientConnectorError, aiohttp.ClientConnectionError,
     aiohttp.ContentTypeError),
    max_time=600,
)
giveup = lambda exception: 400 <= exception.status < 500

response_backoff = backoff.on_exception(backoff.expo,
                                        aiohttp.ClientResponseError,
                                        max_time=600,
                                        giveup=giveup)

timeout_backoff = backoff.on_exception(
    backoff.expo,
    aiohttp.ServerTimeoutError,
    max_time=300,
    max_tries=5
)


default_backoff = timeout_backoff(conn_backoff(response_backoff))


class HikariResponse(TypedDict):
    url: str


@singledispatch
@default_backoff
async def to_producer(file: str | URL) -> HikariResponse:
    url = URL(file) if isinstance(file, str) else file

    async with get_session().get(url) as req:
        filename = url.name
        data = aiohttp.FormData()
        data.add_field("file", req.content, filename=filename)

        async with get_session().post(PRODUCER_UPLOAD_ENDPOINT, data=data) as req:
            return await req.json()


@to_producer.register
@default_backoff
async def _(file: io.IOBase, filename=None) -> HikariResponse:
    if filename is not None:
        file.name = filename  # type: ignore

    headers = {
        "Authorization": f"Bearer {PRODUCER_TOKEN}",
        "Expires": 0,
    }

    async with get_session().post(PRODUCER_UPLOAD_ENDPOINT,
                                  headers=headers, data=dict(file=file)) as req:
        return await req.json()


P = ParamSpec('P')
T = TypeVar('T')


async def run_coro(coro):
    if asyncio.iscoroutine(coro):
        return await coro
    else:
        return coro


def log_time(func: Callable[P, T]) -> Callable[P, T]:
    logger = logging.getLogger(func.__module__)

    @wraps(func)
    async def decorated(*args: P.args, **kwargs: P.kwargs):
        begin = time.monotonic()
        ret = func(*args, **kwargs)
        if asyncio.iscoroutine(ret):
            ret = await ret
        end = time.monotonic()
        logger.debug(f"{func.__name__} took {end - begin:.2f}s")
        return ret

    return decorated  # type: ignore
