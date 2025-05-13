import asyncio
import sys
from collections.abc import Awaitable, Callable
from functools import cache
from typing import Any

from discord_webhook import AsyncDiscordWebhook
from rich import traceback
from rich.console import Console

from nanapi.settings import ERROR_WEBHOOK_URL, INSTANCE_NAME

TRACEBACK_KWARGS: dict[str, Any] = dict(word_wrap=True)


def get_traceback(e: BaseException | None = None) -> traceback.Traceback:
    if e is None:
        return get_traceback_exc()

    return traceback.Traceback.from_exception(type(e), e, e.__traceback__, **TRACEBACK_KWARGS)


def get_traceback_exc() -> traceback.Traceback:
    infos = sys.exc_info()
    assert infos[0] is not None
    return traceback.Traceback.from_exception(*infos, **TRACEBACK_KWARGS)


@cache
def get_console() -> Console:
    return Console(width=78)


def get_traceback_str(trace: traceback.Traceback) -> str:
    console = get_console()
    return ''.join(s.text for s in console.render(trace))


class Paginator:
    def __init__(
        self,
        prefix: str | None = '```',
        suffix: str | None = '```',
        max_size: int = 2000,
        linesep: str = '\n',
    ) -> None:
        self.prefix: str | None = prefix
        self.suffix: str | None = suffix
        self.max_size: int = max_size
        self.linesep: str = linesep
        self.clear()

    def clear(self) -> None:
        """Clears the paginator to have no pages."""
        if self.prefix is not None:
            self._current_page: list[str] = [self.prefix]
            self._count: int = len(self.prefix) + self._linesep_len  # prefix + newline
        else:
            self._current_page = []
            self._count = 0
        self._pages: list[str] = []

    @property
    def _prefix_len(self) -> int:
        return len(self.prefix) if self.prefix else 0

    @property
    def _suffix_len(self) -> int:
        return len(self.suffix) if self.suffix else 0

    @property
    def _linesep_len(self) -> int:
        return len(self.linesep)

    def add_line(self, line: str = '', *, empty: bool = False) -> None:
        """Adds a line to the current page."""
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - 2 * self._linesep_len
        if len(line) > max_page_size:
            raise RuntimeError(f'Line exceeds maximum page size {max_page_size}')

        if self._count + len(line) + self._linesep_len > self.max_size - self._suffix_len:
            self.close_page()

        self._count += len(line) + self._linesep_len
        self._current_page.append(line)

        if empty:
            self._current_page.append('')
            self._count += self._linesep_len

    def close_page(self) -> None:
        """Prematurely terminate a page."""
        if self.suffix is not None:
            self._current_page.append(self.suffix)
        self._pages.append(self.linesep.join(self._current_page))

        if self.prefix is not None:
            self._current_page = [self.prefix]
            self._count = len(self.prefix) + self._linesep_len  # prefix + linesep
        else:
            self._current_page = []
            self._count = 0

    def __len__(self) -> int:
        total = sum(len(p) for p in self._pages)
        return total + self._count

    @property
    def pages(self) -> list[str]:
        """List[:class:`str`]: Returns the rendered list of pages."""
        # we have more than just the prefix in our current page
        if len(self._current_page) > (0 if self.prefix is None else 1):
            self.close_page()
        return self._pages


async def send_webhook(message: str, username: str):
    webhook = AsyncDiscordWebhook(url=ERROR_WEBHOOK_URL, username=username, content=message)
    await webhook.execute()


async def webhook_post_error(error_msg: str, username: str = INSTANCE_NAME):
    paginator = Paginator(max_size=2000)
    for l in error_msg.split('\n'):
        paginator.add_line(l)
    for page in paginator.pages:
        await send_webhook(page, username)


def webhook_exceptions[**P, R](func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    async def wrapper(*args: P.args, **kwargs: P.kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if ERROR_WEBHOOK_URL:
                trace = get_traceback(e)
                msg = f'{get_traceback_str(trace)}\n{func=}'
                asyncio.create_task(webhook_post_error(msg, username=f'{INSTANCE_NAME} - Tasks'))
            raise

    wrapper.__name__ = func.__name__

    return wrapper
