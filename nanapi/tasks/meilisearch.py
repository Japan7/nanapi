import asyncio
import logging

from nanapi.database.anilist.chara_select_all_names import chara_select_all_names
from nanapi.database.anilist.media_select_all_titles import media_select_all_titles
from nanapi.database.anilist.staff_select_all_names import staff_select_all_names
from nanapi.database.waicolle.collection_meili import collection_meili
from nanapi.settings import INSTANCE_NAME, LOG_LEVEL
from nanapi.utils.clients import get_edgedb, get_meilisearch
from nanapi.utils.logs import webhook_exceptions
from nanapi.utils.misc import log_time

logger = logging.getLogger(__name__)


@webhook_exceptions
@log_time
async def feed_meili_medias():
    items = await media_select_all_titles(get_edgedb())
    if len(items) == 0:
        return
    items_dict = [item.model_dump() for item in items]
    logger.debug(f"indexing {len(items_dict)} medias")
    async with get_meilisearch() as client:
        index = client.index(f"{INSTANCE_NAME}_medias")
        await index.update_filterable_attributes(["type"])
        await index.add_documents(items_dict, primary_key="id_al")


@webhook_exceptions
@log_time
async def feed_meili_charas():
    items = await chara_select_all_names(get_edgedb())
    if len(items) == 0:
        return
    items_dict = [item.model_dump() for item in items]
    logger.debug(f"indexing {len(items_dict)} charas")
    async with get_meilisearch() as client:
        index = client.index(f"{INSTANCE_NAME}_charas")
        await index.add_documents(items_dict, primary_key="id_al")


@webhook_exceptions
@log_time
async def feed_meili_staffs():
    items = await staff_select_all_names(get_edgedb())
    if len(items) == 0:
        return
    items_dict = [item.model_dump() for item in items]
    logger.debug(f"indexing {len(items_dict)} staffs")
    async with get_meilisearch() as client:
        index = client.index(f"{INSTANCE_NAME}_staffs")
        await index.add_documents(items_dict, primary_key="id_al")


@webhook_exceptions
async def feed_meili_collections():
    resp = await collection_meili(get_edgedb())
    async with get_meilisearch() as client:
        for group in resp:
            client_id = group.key.client.id
            index = client.index(f"{INSTANCE_NAME}_collections_{client_id}")
            await index.delete_all_documents()
            docs = [
                dict(id=str(collec.id),
                     name=collec.name,
                     author_discord_id=collec.author.user.discord_id)
                for collec in group.elements
            ]
            await index.add_documents(docs, primary_key="id")


async def main():
    await feed_meili_medias()
    await feed_meili_charas()
    await feed_meili_staffs()
    await feed_meili_collections()


if __name__ == '__main__':
    logging.basicConfig(level=LOG_LEVEL)
    asyncio.run(main())
