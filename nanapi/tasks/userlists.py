import asyncio
import logging

from nanapi.database.anilist.account_replace_entries import account_replace_entries
from nanapi.database.anilist.account_select_all import account_select_all
from nanapi.database.anilist.media_select_all_ids import media_select_all_ids
from nanapi.models.anilist import AnilistService, MediaType
from nanapi.settings import LOG_LEVEL
from nanapi.utils.anilist import (
    SERVICE_USER_LIST,
    Userlist,
    malmapper,
    merge_lock,
    update_missing_media,
)
from nanapi.utils.clients import get_edgedb
from nanapi.utils.logs import webhook_exceptions

logger = logging.getLogger(__name__)


@webhook_exceptions
async def refresh_lists() -> None:
    async with merge_lock:
        logger.info('refresh_lists: reloading MALMapper')
        media_ids = await media_select_all_ids(get_edgedb())
        malmapper.load(list(media_ids))

        anilists = await account_select_all(get_edgedb())
        almedias = set[int]()
        logger.info(f'refresh_lists: refreshing {len(anilists)} users')

        for al in anilists:
            service = AnilistService(al.service)
            userlist = SERVICE_USER_LIST[service](al.username)
            for media_type in MediaType:
                try:
                    user_entries = await refresh_list(userlist, media_type)
                    almedias.update(e.id_al for e in user_entries)
                except Exception as e:
                    logger.exception(e)

            logger.info(f'refreshed entries for {al.username}')


async def refresh_list(userlist: Userlist, media_type: MediaType):
    logger_list = f'{userlist.service}/{userlist.username}/{media_type}'
    logger.info(f'refresh_list: fetching {logger_list}')
    entries = await userlist.refresh(media_type)
    medias = {i.id_al for i in entries}
    logger.info(f'refresh_list: {logger_list} fetched with {len(entries)} entries')

    if len(entries) > 0:
        await update_missing_media(medias)
        logger.info('updated medias for entries')
        edgedb_data = userlist.to_edgedb(media_type, entries)
        _ = await account_replace_entries(get_edgedb(), **edgedb_data)
    return entries


async def main():
    await refresh_lists()


if __name__ == '__main__':
    logging.basicConfig(level=LOG_LEVEL)
    asyncio.run(main())
