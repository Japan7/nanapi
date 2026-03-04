import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta

from fastapi import FastAPI, Request, status
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute

from nanapi.routers import (
    ai,
    amq,
    anilist,
    calendar,
    client,
    discord,
    histoire,
    pot,
    presence,
    projection,
    quizz,
    reminder,
    role,
    user,
    waicolle,
    wrapped,
)
from nanapi.settings import (
    ERROR_WEBHOOK_URL,
    FASTAPI_CONFIG,
    INSTANCE_NAME,
    LOG_LEVEL,
    PROFILING,
)
from nanapi.utils.logs import get_traceback, get_traceback_str, webhook_post_error
from nanapi.utils.waicolle import load_rolls

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute):
    tag_prefix = f'{route.tags[0]}_' if route.tags else ''
    return f'{tag_prefix}{route.name}'.casefold()


async def daily_tasks():
    # reload rolls every day
    # the rolls for the current day should be already prepared,
    # but it should prepare the rolls for the next day
    logger.info('[daily] preloading rolls')
    asyncio.create_task(load_rolls())


async def daily_loop():
    while True:
        tomorrow = date.today() + timedelta(days=1)
        t = datetime.fromordinal(tomorrow.toordinal()) - datetime.now()
        await asyncio.sleep(t.total_seconds())
        await daily_tasks()


async def startup():
    # preload rolls so it might not take too much time to load
    # when someone needs it
    logger.info('[startup] preloading rolls')
    asyncio.create_task(load_rolls())
    asyncio.create_task(daily_loop())


async def cleanup():
    pass


class HypercornLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        if record.name.startswith('hypercorn'):
            return False

        return super().filter(record)


@asynccontextmanager
async def lifespan(_: FastAPI):
    format = '[%(asctime)s] [%(process)d] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s'
    handler = logging.StreamHandler(sys.stderr)
    datefmt = '%Y-%m-%d %H:%M:%S %z'
    handler.setFormatter(logging.Formatter(format, datefmt=datefmt))
    # would get duplicate logs otherwise
    handler.addFilter(HypercornLogFilter())

    logging.basicConfig(level=LOG_LEVEL, handlers=[handler])

    await startup()
    yield
    await cleanup()


app = FastAPI(
    title=INSTANCE_NAME,
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
    **FASTAPI_CONFIG,
)

app.add_middleware(GZipMiddleware)
if PROFILING:
    from nanapi.utils.fastapi import ProfilerMiddleware

    app.add_middleware(ProfilerMiddleware, fastapi_app=app)


app.include_router(ai.router)
app.include_router(amq.router)
app.include_router(anilist.router)
app.include_router(calendar.router)
app.include_router(client.router)
app.include_router(discord.router)
app.include_router(histoire.router)
app.include_router(pot.router)
app.include_router(presence.router)
app.include_router(projection.router)
app.include_router(quizz.router)
app.include_router(reminder.router)
app.include_router(role.router)
app.include_router(user.router)
app.include_router(waicolle.router)
app.include_router(wrapped.router)


@app.get('/health', status_code=status.HTTP_204_NO_CONTENT)
def ping():
    return


@app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
async def internal_server_error_handler(request: Request, e: Exception):
    if ERROR_WEBHOOK_URL:
        trace = get_traceback(e)
        msg = f'{get_traceback_str(trace)}\n{request.method=}\n{request.url=}'
        asyncio.create_task(webhook_post_error(msg))
    raise e
