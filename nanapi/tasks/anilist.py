import argparse
import asyncio
import logging
import sys
import time
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass
from itertools import batched, chain
from typing import TypedDict

import nanapi.settings as settings
from nanapi.database.anilist.c_edge_merge_multiple import (
    CEdgeMergeMultipleEdges,
    c_edge_merge_multiple,
)
from nanapi.database.anilist.chara_merge_multiple import chara_merge_multiple
from nanapi.database.anilist.chara_select_all_ids import chara_select_all_ids
from nanapi.database.anilist.chara_update import chara_update
from nanapi.database.anilist.media_merge_combined_charas import media_merge_combined_charas
from nanapi.database.anilist.media_select_all_ids import media_select_all_ids
from nanapi.database.anilist.staff_select_all_ids import staff_select_all_ids
from nanapi.database.anilist.staff_update_multiple import staff_update_multiple
from nanapi.database.anilist.tag_merge_multiple import tag_merge_multiple
from nanapi.models.anilist import ALMedia, ALStaff
from nanapi.tasks.userlists import refresh_lists
from nanapi.utils.anilist import (
    al_set_high_priority,
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
    tags = await get_tags()
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
    medias_info: dict[int, ALMedia] = {}
    media_characters: dict[int, set[int]] = defaultdict(set)
    while to_update:
        batches = list(batched(to_update, 50))
        logger.info(f'refreshing {len(to_update)} medias')

        to_merge: list[int] = []

        for mbatch in batches:
            medias = await fetch_media(*mbatch, page=page)

            to_update.difference_update(mbatch)
            for m in medias:
                assert m.characters is not None
                if page == 1:
                    medias_info[m.id] = m

                media_characters[m.id].update(c.id for c in m.characters.nodes)

                if m.characters.pageInfo.hasNextPage:
                    to_update.add(m.id)
                else:
                    to_merge.append(m.id)

        characters = set(chain.from_iterable(media_characters.values()))

        logger.info(f'merging characters from {len(media_characters)} medias')
        await update_missing_characters(characters)
        for media_id in to_merge:
            charas = media_characters.pop(media_id)
            _ = await media_merge_combined_charas(
                get_edgedb(),
                media=medias_info.pop(media_id).to_edgedb(),
                characters=list(charas),
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
    tx = get_edgedb()

    charas_db = await chara_select_all_ids(tx)
    to_update = {i.id_al for i in charas_db if i.last_update == 0}
    to_update |= {
        i.id_al
        for i in charas_db[: len(charas_db) // 20]
        if i.last_update != 0 and i.last_update < time.time() - 3600 * 24
    }
    updated = set[int]()

    page = 1
    chara_edges: list[CEdgeMergeMultipleEdges] = []
    medias = set[int]()
    voice_actors = set[int]()
    while to_update:
        batches = list(batched(to_update, 50))
        logger.info(f'refreshing {len(to_update)} charas')

        for cbatch in batches:
            charas = await fetch_chara(*cbatch, page=page)

            to_update.difference_update(cbatch)
            for c in charas:
                updated.add(c.id)
                assert c.media is not None
                for e in c.media.edges:
                    medias.add(e.node.id)
                    voice_actors |= {va.id for va in e.voiceActors}
                    chara_edges.append(
                        CEdgeMergeMultipleEdges(
                            [va.id for va in e.voiceActors], c.id, e.node.id, e.characterRole
                        )
                    )

                if c.media.pageInfo.hasNextPage:
                    to_update.add(c.id)

            if page == 1:
                _ = await chara_merge_multiple(tx, characters=[c.to_edgedb() for c in charas])

        page += 1

    # media links will be linked the next time refresh_medias runs
    await update_missing_media(medias)
    await update_missing_staff(voice_actors)
    logger.info(f'adding {len(chara_edges)} character edges')
    _ = await c_edge_merge_multiple(tx, edges=chara_edges)
    _ = await chara_update(tx, characters=list(updated), last_update=int(time.time()))


@webhook_exceptions
async def refresh_staffs() -> None:
    staff_db = await staff_select_all_ids(get_edgedb())
    to_update = {i.id_al for i in staff_db if i.last_update == 0}
    to_update |= {
        i.id_al
        for i in staff_db[: len(staff_db) // 10]
        if i.last_update != 0 and i.last_update < time.time() - 3600 * 24
    }

    staff_infos: dict[int, ALStaff] = {}
    page = 1
    while to_update:
        batches = list(batched(to_update, 50))
        logger.info(f'refreshing {len(to_update)} staffs')

        charas = set[int]()
        to_merge: list[ALStaff] = []

        for sbatch in batches:
            staffs = await fetch_staff(*sbatch, page=page)

            to_update.difference_update(sbatch)
            for s in staffs:
                assert s.characters is not None
                charas |= {c.id for c in s.characters.nodes}

                if s.characters.pageInfo.hasNextPage:
                    if page == 1:
                        staff_infos[s.id] = s
                    to_update.add(s.id)
                else:
                    to_merge.append(staff_infos.get(s.id, s))
                    with suppress(KeyError):
                        del staff_infos[s.id]

        await update_missing_characters(charas)
        _ = await staff_update_multiple(
            get_edgedb(),
            staffs=[s.to_edgedb() for s in to_merge],
            last_update=int(time.time()),
        )

        page += 1


@dataclass
class Args:
    high_priority: bool = False


async def main():
    parser = argparse.ArgumentParser('anilist_tasks')
    _ = parser.add_argument(
        '--high-priority',
        help=(
            'for development purposes only, '
            'doesn’t keep a budget of requests for interactive actions.'
        ),
        action=argparse.BooleanOptionalAction,
    )
    args = Args()
    _ = parser.parse_args(sys.argv[1:], namespace=args)

    if args.high_priority:
        logger.info('running this task with higher priority on Anilist API call budget')
        al_set_high_priority()

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
    logging.basicConfig(level=settings.LOG_LEVEL)
    asyncio.run(main())
