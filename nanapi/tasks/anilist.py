import asyncio
import logging
import time
from contextlib import suppress
from itertools import batched, chain
from typing import TypedDict

from nanapi.database.anilist.c_edge_merge_multiple import c_edge_merge_multiple
from nanapi.database.anilist.chara_merge_multiple import chara_merge_multiple
from nanapi.database.anilist.chara_select_all_ids import chara_select_all_ids
from nanapi.database.anilist.media_merge_combined_charas import media_merge_combined_charas
from nanapi.database.anilist.media_select_all_ids import media_select_all_ids
from nanapi.database.anilist.staff_select_all_ids import staff_select_all_ids
from nanapi.database.anilist.staff_update_multiple import staff_update_multiple
from nanapi.database.anilist.tag_merge_multiple import tag_merge_multiple
from nanapi.models.anilist import ALMedia, ALStaff
from nanapi.settings import LOG_LEVEL
from nanapi.tasks.userlists import refresh_lists
from nanapi.utils.anilist import (
    fetch_chara,
    fetch_media,
    fetch_staff,
    get_tags,
    update_missing_characters,
    update_missing_media,
    update_missing_staff,
)
from nanapi.utils.clients import get_edgedb
from nanapi.utils.logs import webhook_exceptions

logger = logging.getLogger(__name__)


@webhook_exceptions
async def refresh_tags():
    tags = await get_tags(al_low_priority=True)
    await tag_merge_multiple(get_edgedb(), tags=[tag.to_edgedb() for tag in tags])


@webhook_exceptions
async def refresh_medias() -> None:
    media_ids = await media_select_all_ids(get_edgedb())
    to_update = {i.id_al for i in media_ids if i.last_update == 0}
    to_update |= {
        i.id_al
        for i in media_ids[: len(media_ids) // 10]
        if i.last_update != 0 and i.last_update < time.time() - 3600 * 24
    }

    page = 1
    medias_pages: dict[int, ALMedia] = {}
    while to_update:
        batches = list(batched(to_update, 50))
        logger.info(f'refreshing {len(to_update)} medias')

        for mbatch in batches:
            medias = await fetch_media(*mbatch, page=page, low_priority=True)
            to_merge: list[ALMedia] = []

            to_update.difference_update(mbatch)
            for m in medias:
                assert m.characters is not None
                if page == 1:
                    media = m
                else:
                    media = medias_pages[m.id]
                    assert media.characters is not None
                    media.characters.nodes.extend(m.characters.nodes)

                if m.characters.pageInfo.hasNextPage:
                    medias_pages[m.id] = media
                    to_update.add(m.id)
                else:
                    with suppress(KeyError):
                        del medias_pages[m.id]
                    to_merge.append(media)

            characters = set(
                i.id
                for i in chain.from_iterable(
                    m.characters.nodes for m in to_merge if m.characters is not None
                )
            )

            logger.info(f'merging characters from {len(to_merge)} medias')
            await update_missing_characters(characters, low_priority=True)
            for media in to_merge:
                _ = await media_merge_combined_charas(
                    get_edgedb(),
                    media=media.to_edgedb(),
                    characters=list(characters),
                    last_update=int(time.time()),
                )

        page += 1


class CharacterEdge(TypedDict):
    character_id: int
    voice_actor_ids: list[int]
    media_id: int
    character_role: str | None


@webhook_exceptions
async def refresh_charas() -> None:
    db = get_edgedb()

    async for tx in db.transaction():
        async with tx:
            charas_db = await chara_select_all_ids(tx)
            to_update = {i.id_al for i in charas_db if i.last_update == 0}
            to_update |= {
                i.id_al
                for i in charas_db[: len(charas_db) // 10]
                if i.last_update != 0 and i.last_update < time.time() - 3600 * 24
            }

            page = 1
            chara_edges: list[CharacterEdge] = []
            medias = set[int]()
            voice_actors = set[int]()
            while to_update:
                batches = list(batched(to_update, 50))
                logger.info(f'refreshing {len(to_update)} charas')

                for cbatch in batches:
                    charas = await fetch_chara(*cbatch, page=page, low_priority=True)

                    to_update.difference_update(cbatch)
                    for c in charas:
                        assert c.media is not None
                        for e in c.media.edges:
                            medias.add(e.node.id)
                            voice_actors |= {va.id for va in e.voiceActors}
                            chara_edges.append(
                                {
                                    'character_id': c.id,
                                    'voice_actor_ids': [va.id for va in e.voiceActors],
                                    'media_id': e.node.id,
                                    'character_role': e.characterRole,
                                }
                            )

                        if c.media.pageInfo.hasNextPage:
                            to_update.add(c.id)

                    if page == 1:
                        _ = await chara_merge_multiple(
                            tx, characters=[c.to_edgedb(is_updating=True) for c in charas]
                        )

                page += 1

            # media links will be linked the next time refresh_medias runs
            await update_missing_media(medias, low_priority=True)
            await update_missing_staff(voice_actors, low_priority=True)
            _ = await c_edge_merge_multiple(tx, edges=chara_edges)


@webhook_exceptions
async def refresh_staffs() -> None:
    async for tx in get_edgedb().transaction():
        async with tx:
            staff_db = await staff_select_all_ids(get_edgedb())
            to_update = {i.id_al for i in staff_db if i.last_update == 0}
            to_update |= {
                i.id_al
                for i in staff_db[: len(staff_db) // 10]
                if i.last_update != 0 and i.last_update < time.time() - 3600 * 24
            }

            staff_pages: dict[int, ALStaff] = {}
            page = 1
            while to_update:
                batches = list(batched(to_update, 50))
                logger.info(f'refreshing {len(to_update)} staffs')

                for sbatch in batches:
                    staffs = await fetch_staff(*sbatch, page=page, low_priority=True)
                    to_merge: list[ALStaff] = []

                    charas = set[int]()
                    to_update.difference_update(sbatch)
                    for s in staffs:
                        assert s.characters is not None
                        staff = staff_pages.get(s.id, s)

                        charas |= {c.id for c in s.characters.nodes}

                        if s.characters.pageInfo.hasNextPage:
                            staff_pages[s.id] = staff
                            to_update.add(s.id)
                        else:
                            with suppress(KeyError):
                                del staff_pages[s.id]
                            to_merge.append(staff)

                    await update_missing_characters(charas, low_priority=True)
                    _ = await staff_update_multiple(
                        get_edgedb(),
                        staffs=[s.to_edgedb() for s in to_merge],
                        last_update=int(time.time()),
                    )

                page += 1


async def main():
    logger.info('refreshing tags')
    await refresh_tags()
    logger.info('refreshing lists')
    await refresh_lists()
    logger.info('refreshing medias')
    await refresh_medias()
    logger.info('refreshing charas')
    await refresh_charas()
    logger.info('refreshing staffs')
    await refresh_staffs()


if __name__ == '__main__':
    logging.basicConfig(level=LOG_LEVEL)
    asyncio.run(main())
