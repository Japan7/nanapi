import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import timedelta
from itertools import count, filterfalse
from typing import Any, Generator, Generic, Optional, Self, Type, TypeVar

import aiohttp
import numpy as np
import orjson
import polars as pl
from asyncache import cached
from cachetools import TTLCache
from edgedb import AsyncIOExecutor
from pydantic import TypeAdapter
from sklearn import preprocessing
from sklearn.decomposition import TruncatedSVD
from toolz.curried import concat
from toolz.itertoolz import partition_all

from nanapi.database.anilist.c_edge_merge_combined_by_chara import c_edge_merge_combined_by_chara
from nanapi.database.anilist.c_edge_merge_multiple import c_edge_merge_multiple
from nanapi.database.anilist.chara_merge_multiple import chara_merge_multiple
from nanapi.database.anilist.entry_select_all import entry_select_all
from nanapi.database.anilist.media_merge_combined_charas import media_merge_combined_charas
from nanapi.database.anilist.media_merge_multiple import media_merge_multiple
from nanapi.database.anilist.media_select_all_ids import MediaSelectAllIdsResult
from nanapi.database.anilist.staff_merge_combined_medias_charas import (
    staff_merge_combined_medias_charas,
)
from nanapi.database.anilist.staff_merge_multiple import staff_merge_multiple
from nanapi.models.anilist import (
    ALBaseModel,
    ALCharacter,
    ALMedia,
    ALMediaEdge,
    ALPageInfo,
    ALStaff,
    ALStaffCharacterEdge,
    AnilistService,
    MALListResp,
    MALListRespDataEntry,
    MediaTag,
    MediaType,
)
from nanapi.settings import LOW_PRIORITY_THRESH, MAL_CLIENT_ID
from nanapi.utils.clients import get_edgedb, get_session
from nanapi.utils.misc import default_backoff

logger = logging.getLogger(__name__)

# https://studio.apollographql.com/sandbox/explorer/
AL_URL = 'https://graphql.anilist.co'

JOB_TIMEOUT = 0.1

MERGE_COMBINED_MAX_SIZE = 100

page_info = """
pageInfo {
    currentPage
    hasNextPage
}
"""

base_fields = """
id
favourites
siteUrl
"""

media_fields = """
%s
type
idMal
title {
    userPreferred
    english
    native
}
synonyms
description
status
season
seasonYear
episodes
duration
chapters
coverImage {
    extraLarge
    color
}
popularity
isAdult
genres
tags {
    id
    rank
}
""" % base_fields

chara_fields = """
%s
name {
    userPreferred
    alternative
    alternativeSpoiler
    native
}
image {
    large
}
description(asHtml: true)
gender
dateOfBirth {
    year
    month
    day
}
age
""" % base_fields

staff_fields = """
%s
name {
    userPreferred
    alternative
    native
}
image {
    large
}
description(asHtml: true)
gender
dateOfBirth {
    year
    month
    day
}
dateOfDeath {
    year
    month
    day
}
age
""" % base_fields

tag_fields = """
id
name
description
category
isAdult
"""


class ALRateLimit(Exception):

    def __init__(self, reset_at: int):
        super().__init__(f"Rate limited until {reset_at}")
        self.reset_at = reset_at

    @property
    def reset_in(self):
        return self.reset_at - time.time()


class ALAPI:
    RATE_LIMIT = 90

    def __init__(self):
        self.low_priority_ready = asyncio.Event()
        self.low_priority_ready.set()
        self.reset_task: Optional[asyncio.Task] = None
        self._reset_at = 0
        self.last_request_time = 0
        self._remaining = ALAPI.RATE_LIMIT
        # NOTE: just so low priority tasks don't overshoot the threshold too much
        self.low_priority_semaphore = asyncio.Semaphore(2)

    async def reset(self):
        loop = asyncio.get_running_loop()
        while self.last_request_time + 60 > loop.time():
            wait_time = (self.last_request_time + 60) - loop.time()
            logger.debug(f"ALAPI reset: sleeping for {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.remaining = ALAPI.RATE_LIMIT

    @property
    def reset_at(self):
        return self._reset_at

    @reset_at.setter
    def reset_at(self, value):
        value = int(value)
        self._reset_at = value + 1

    @property
    def reset_in(self):
        normal_reset_in = self.reset_at - time.time()
        if normal_reset_in >= 0:
            return normal_reset_in

        # it's odd and I'd rather be safe in that case
        return max(self.last_request_time + 60 - time.time(), 1)

    @reset_in.setter
    def reset_in(self, value):
        self._reset_at = time.time() + value

    @property
    def remaining(self):
        return self._remaining

    @remaining.setter
    def remaining(self, value):
        value = int(value)
        logger.debug(f"ALAPI rate limit: {value} remaining requests")
        self._remaining = value
        if value > LOW_PRIORITY_THRESH:
            self.low_priority_ready.set()
        else:
            self.low_priority_ready.clear()

        loop = asyncio.get_running_loop()
        self.last_request_time = loop.time()
        if self.reset_task is None or self.reset_task.done():
            self.reset_task = asyncio.create_task(self.reset())

    async def _call(self,
                    json_query: bytes,
                    raise_rate_limit=False,
                    timeout: aiohttp.ClientTimeout | None = None):
        while True:
            try:
                if self.reset_at > time.time():
                    raise ALRateLimit(self.reset_at)

                headers = {'Content-Type': "application/json"}
                async with get_session().post(AL_URL,
                                              timeout=timeout,
                                              data=json_query,
                                              headers=headers) as resp:
                    if 'X-RateLimit-Remaining' in resp.headers:
                        self.remaining = resp.headers['X-RateLimit-Remaining']
                    if reset_at := resp.headers.get('X-RateLimit-Reset'):
                        self.reset_at = int(reset_at)
                    elif reset_in := resp.headers.get('Retry-After'):
                        self.reset_in = int(reset_in)

                    if resp.status == 429 and not raise_rate_limit:
                        raise ALRateLimit(self.reset_at)

                    if resp.status == 400:
                        logger.info(await resp.text())

                    resp.raise_for_status()

                    try:
                        raw_resp = await resp.read()
                        json_data = orjson.loads(raw_resp)
                    except Exception:
                        logger.error(await resp.text())
                        raise

                    if 'errors' in json_data:
                        raise RuntimeError(str(json_data['errors']))

                    return json_data
            except ALRateLimit:
                if raise_rate_limit:
                    raise
                else:
                    logger.debug(
                        f"ALAPI rate limit: reached, sleep for {self.reset_in:.2f}s"
                    )
                    await asyncio.sleep(self.reset_in)

    @default_backoff
    async def __call__(self,
                       json: dict[str, Any],
                       raise_rate_limit=False,
                       low_priority=False,
                       timeout: aiohttp.ClientTimeout | None = None):
        json_query = orjson.dumps(json)

        logger.debug(f"ALAPI call: {low_priority=}")

        if low_priority:
            async with self.low_priority_semaphore:
                await self.low_priority_ready.wait()
                return await self._call(json_query, raise_rate_limit, timeout)
        else:
            return await self._call(json_query, raise_rate_limit, timeout)

    def timeout_anilist_loader(self):
        if reset_at := self.reset_at:
            reset_in = reset_at - time.time()
            if reset_in > JOB_TIMEOUT:
                return reset_in

        return JOB_TIMEOUT


anilist_api = ALAPI()


class MALMapper(dict):

    def __init__(self):
        super().__init__()
        for k in MediaType:
            self[k] = {}

    def load(self, media_ids: list[MediaSelectAllIdsResult]):
        for m in media_ids:
            if m.type is not None and m.id_mal is not None:
                self[MediaType(m.type)][m.id_mal] = m.id_al


malmapper = MALMapper()


#########
# Lists #
#########
class Userlist:
    service: AnilistService

    def __init__(self, username: str):
        self.username = username

    async def refresh(
            self,
            media_type: MediaType,
            al_low_priority: bool = False) -> tuple[list[dict], set[ALMedia]]:
        return [], set()

    def to_edgedb(self, media_type: MediaType, entries: list[dict],
                  medias: set[ALMedia]) -> dict[str, Any]:
        nodes = [m.to_edgedb() for m in medias]
        edgedb_data = dict(medias=nodes,
                           service=self.service.value,
                           username=self.username,
                           type=media_type.value,
                           entries=entries)
        return edgedb_data

    def __str__(self):
        return f"<{self.__class__.__name__} {self.username=}>"

    __repr__ = __str__


class ALUserlist(Userlist):
    service = AnilistService.ANILIST

    async def refresh(self, media_type: MediaType, al_low_priority=False):
        await super().refresh(media_type)

        # fetch updated list
        entries = await self.fetch_entries(media_type, al_low_priority)

        new_entries = []
        new_medias = set()
        for entry in entries:
            almedia = ALMedia.model_validate(entry['media'])
            new_entries.append(
                dict(id_al=almedia.id,
                     status=entry['status'],
                     progress=entry['progress'],
                     score=entry['score']))
            new_medias.add(almedia)

        return new_entries, new_medias

    async def fetch_entries(self, media_type, al_low_priority):
        query = """
        query ($username: String, $type: MediaType) {
            MediaListCollection(userName: $username, type: $type) {
                lists {
                    entries {
                        score(format: POINT_10_DECIMAL)
                        status
                        progress
                        media {
                            %s
                            characters {
                                %s
                                nodes {
                                    %s
                                }
                            }
                        }
                    }
                }
            }
        }
        """ % (media_fields, page_info, chara_fields)
        variables = {
            'username': self.username,
            'type': media_type,
        }

        jsonData = await anilist_api(
            {
                'query': query,
                'variables': variables
            },
            timeout=aiohttp.ClientTimeout(total=300),
            low_priority=al_low_priority,
        )

        entries = concat(
            l['entries']
            for l in jsonData['data']['MediaListCollection']['lists'])

        return entries

    def __str__(self):
        return f"https://anilist.co/user/{self.username}"


class MALUserlist(Userlist):
    service = AnilistService.MYANIMELIST

    MAL_STATUS = {
        'watching': 'CURRENT',
        'reading': 'CURRENT',
        'completed': 'COMPLETED',
        'on_hold': 'PAUSED',
        'dropped': 'DROPPED',
        'plan_to_watch': 'PLANNING',
        'plan_to_read': 'PLANNING',
    }

    refresh_lock = asyncio.Lock()

    async def refresh(self, media_type: MediaType, al_low_priority=False):
        await super().refresh(media_type)

        for _ in range(3):
            try:
                userlist = await self.fetch_list(self.username, media_type)
                break
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(1)
        else:
            logger.error(f"MALUserlist: refresh failed for {self.username}")
            return [], set()

        al_ids, new_medias = await self.get_al_ids(
            media_type,
            set(entry.node.id for entry in userlist),
            low_priority=al_low_priority)

        new_entries = []
        for entry in userlist:
            if entry.node.id is not None:
                repeating = (entry.list_status.is_rewatching
                             if media_type == MediaType.ANIME else
                             entry.list_status.is_rereading)
                status = ('REPEATING' if repeating else
                          self.MAL_STATUS[entry.list_status.status])

                progress = (entry.list_status.num_episodes_watched
                            if media_type is MediaType.ANIME else
                            entry.list_status.num_chapters_read)

                if (id_al := al_ids.get(entry.node.id, None)):
                    new_entries.append(
                        dict(id_al=id_al,
                             status=status,
                             progress=progress,
                             score=entry.list_status.score))

        return new_entries, new_medias

    @classmethod
    async def fetch_list(cls, username: str, media_type: MediaType):
        async with cls.refresh_lock:
            url = f"https://api.myanimelist.net/v2/users/{username}/{media_type.lower()}list"
            headers = {'X-MAL-CLIENT-ID': MAL_CLIENT_ID}
            entries: list[MALListRespDataEntry] = []
            for offset in count(0, 1000):
                params = dict(limit=1000, offset=offset, fields='list_status')
                async with get_session().get(url,
                                             params=params,
                                             headers=headers) as resp:
                    resp.raise_for_status()

                    try:
                        raw_resp = await resp.read()
                        parsed = MALListResp.model_validate_json(raw_resp)
                    except Exception:
                        logger.error(await resp.text())
                        raise

                    entries += parsed.data

                    if parsed.paging.next is None:
                        break
            return entries

    @classmethod
    async def get_al_ids(
        cls,
        media_type: MediaType,
        ids_mal: set[int],
        low_priority: bool = False
    ) -> tuple[dict[int, int | None], set[ALMedia]]:
        to_fetch = [
            id_mal for id_mal in ids_mal if id_mal not in malmapper[media_type]
        ]

        new_medias = set()
        if to_fetch:
            query = """
            query ($idMal_in: [Int], $type: MediaType) {
                Page {
                    media(idMal_in: $idMal_in, type: $type) {
                        %s
                        characters {
                            %s
                            nodes {
                                %s
                            }
                        }
                    }
                }
            }
            """ % (media_fields, page_info, chara_fields)
            for sub_to_fetch in partition_all(50, to_fetch):
                variables = {
                    'idMal_in': sub_to_fetch,
                    'type': media_type,
                }
                try:
                    jsonData = await anilist_api(
                        {
                            'query': query,
                            'variables': variables
                        },
                        low_priority=low_priority)
                    for entry in jsonData['data']['Page']['media']:
                        almedia = ALMedia.model_validate(entry)
                        new_medias.add(almedia)
                except aiohttp.ClientResponseError as e:
                    if e.status == 404:
                        msg = f"MAL ids {ids_mal} not found on AniList"
                        logger.info(msg)
                    else:
                        raise

        return {
            id_mal: malmapper[media_type].get(id_mal, None)
            for id_mal in ids_mal
        }, new_medias

    def __str__(self):
        return f"https://myanimelist.net/profile/{self.username}"


SERVICE_USER_LIST: dict[AnilistService, Type[Userlist]] = {
    AnilistService.ANILIST: ALUserlist,
    AnilistService.MYANIMELIST: MALUserlist,
}


async def get_tags(al_low_priority: bool = False) -> list[MediaTag]:
    query = """
    query {
        MediaTagCollection {
            %s
        }
    }
    """ % tag_fields
    jsonData = await anilist_api(dict(query=query),
                                 low_priority=al_low_priority)
    tags = TypeAdapter(list[MediaTag]).validate_python(
        jsonData['data']['MediaTagCollection'])
    return tags


#############
# Multitons #
#############
@dataclass(slots=True, frozen=True)
class ALMultitons:
    medias: dict[int, 'Media'] = field(default_factory=dict)
    charas: dict[int, 'Chara'] = field(default_factory=dict)
    staffs: dict[int, 'Staff'] = field(default_factory=dict)
    name: str | None = None

    async def edgedb_merge(self,
                           executor: AsyncIOExecutor,
                           full: bool = False,
                           low_priority=True):
        await self.edgedb_merge_medias(executor,
                                       full=full,
                                       low_priority=low_priority)
        await self.edgedb_merge_charas(executor,
                                       full=full,
                                       low_priority=low_priority)
        await self.edgedb_merge_staffs(executor,
                                       full=full,
                                       low_priority=low_priority)

    async def edgedb_merge_medias(self,
                                  executor: AsyncIOExecutor,
                                  full: bool = False,
                                  low_priority: bool = True):
        async with merge_lock:
            medias = set(self.medias.values())
            logger.info(f"{self!r}: merging medias")
            i = 0
            failed = []
            async for m in Media.load(medias,
                                      full=full,
                                      low_priority=low_priority):
                try:
                    await m.edgedb_merge(executor)
                    del self.medias[m.id]
                    i += 1
                    logger.debug(f"{self!r}: merged {i}/{len(medias)} medias, {failed=!r}")
                except Exception as e:
                    failed.append(m.id)
                    logger.error(f"{self!r}: Media[{m.id}] failed to merge")
                    logger.exception(e)
            logger.info(f"{self!r}: merge finished at {i}/{len(medias)} medias")

    async def edgedb_merge_charas(self,
                                  executor: AsyncIOExecutor,
                                  full: bool = False,
                                  low_priority: bool = True):
        async with merge_lock:
            charas = set(self.charas.values())
            logger.info(f"{self!r}: merging charas")
            i = 0
            failed = []
            async for c in Chara.load(charas,
                                      full=full,
                                      low_priority=low_priority):
                try:
                    await c.edgedb_merge(executor)
                    del self.charas[c.id]
                    i += 1
                    logger.debug(f"{self!r}: merged {i}/{len(charas)} charas, {failed=!r}")
                except Exception as e:
                    failed.append(c.id)
                    logger.error(f"{self!r}: Chara[{c.id}] failed to merge")
                    logger.exception(e)
            logger.info(f"{self!r}: merge finished at {i}/{len(charas)} charas")

    async def edgedb_merge_staffs(self,
                                  executor: AsyncIOExecutor,
                                  full: bool = False,
                                  low_priority: bool = True):
        async with merge_lock:
            staffs = set(self.staffs.values())
            logger.info(f"{self!r}: merging staffs")
            i = 0
            failed = []
            async for s in Staff.load(staffs,
                                      full=full,
                                      low_priority=low_priority):
                try:
                    await s.edgedb_merge(executor)
                    del self.staffs[s.id]
                    i += 1
                    logger.debug(f"{self!r}: merged {i}/{len(staffs)} staffs, {failed=!r}")
                except Exception as e:
                    failed.append(s.id)
                    logger.error(f"{self!r}: Staff[{s.id}] failed to merge")
                    logger.exception(e)
            logger.info(f"{self!r}: merge finished at {i}/{len(staffs)} staffs")

    def clear_all(self):
        self.medias.clear()
        self.charas.clear()
        self.staffs.clear()

    def __repr__(self) -> str:
        return (f"<ALMultitons {self.name=} "
                f"{len(self.medias)=} {len(self.charas)=} {len(self.staffs)=}>")


merge_lock = asyncio.Lock()

T = TypeVar('T', bound=ALBaseModel)


class ALEntity(ABC, Generic[T]):
    ALMULTITONS_KEY: str

    def __init__(self, multitons: ALMultitons, id_al: int) -> None:
        self.multitons = multitons
        self.id = id_al
        self._aldata: T | None = None
        self.last_pageinfo: ALPageInfo | None = None
        self.complete = asyncio.Event()

    @property
    def aldata(self) -> T:
        if self._aldata is None:
            raise RuntimeError("Not loaded")
        return self._aldata

    @property
    def current_page(self) -> int:
        if self.last_pageinfo is None:
            return 0
        return self.last_pageinfo.currentPage

    @abstractmethod
    def feed_page(self, value: T) -> None:
        ...

    @abstractmethod
    async def edgedb_merge(self, executor: AsyncIOExecutor) -> None:
        ...

    def __hash__(self) -> int:
        return hash((self.id, self.complete.is_set()))

    @classmethod
    def get(cls, multitons: ALMultitons, id: int) -> Self:
        if id is None:
            raise TypeError("id cannot be None")

        if id not in getattr(multitons, cls.ALMULTITONS_KEY):
            getattr(multitons, cls.ALMULTITONS_KEY)[id] = cls(multitons, id)

        return getattr(multitons, cls.ALMULTITONS_KEY)[id]

    @classmethod
    @abstractmethod
    async def fetch_page(cls,
                         items: set[Self],
                         page: int,
                         low_priority: bool = False) -> set[Self]:
        ...

    @classmethod
    @abstractmethod
    async def load(cls,
                   items: set[Self],
                   full: bool = True,
                   low_priority=False,
                   _start_page: int = 1) -> Generator[Self, None, None]:
        ...


def is_complete(d: ALEntity) -> bool:
    return d.complete.is_set()


#########
# Media #
#########
class Media(ALEntity[ALMedia]):
    ALMULTITONS_KEY: str = 'medias'

    def __init__(self, multitons: ALMultitons, id_al: int) -> None:
        super().__init__(multitons, id_al)
        self.characters: set[Chara] = set()

    @property
    def media_type(self) -> MediaType:
        return MediaType(self.aldata.type)

    def feed_page(self, value: ALMedia) -> None:
        if self.complete.is_set():
            return

        if self._aldata is None:
            self._aldata = value

        if value.characters is not None:
            new_page = value.characters.pageInfo.currentPage

            if new_page > self.current_page:
                self.last_pageinfo = value.characters.pageInfo

                for charaData in value.characters.nodes:
                    chara = Chara.get(self.multitons, charaData.id)
                    chara.feed_page(charaData)
                    self.characters.add(chara)

                if (not self.last_pageinfo.hasNextPage or
                        len(value.characters.nodes) == 0):
                    self.complete.set()

    async def edgedb_merge(self, executor: AsyncIOExecutor):
        media_data = self.aldata.to_edgedb()
        charas_datas = [chara.aldata.to_edgedb() for chara in self.characters]

        logger.debug(
            f"Media[{self.id}]: merging with {len(charas_datas)} charas")
        await media_merge_combined_charas(executor,
                                          media=media_data,
                                          characters=charas_datas)

    @classmethod
    async def fetch_page(cls,
                         items: set['Media'],
                         page: int,
                         low_priority: bool = False) -> set['Media']:
        medias_dict = {m.id: m for m in items}
        found = set()

        query = """
        query ($idIn: [Int], $page: Int) {
            Page {
                media(id_in: $idIn) {
                    %s
                    characters(page: $page) {
                        %s
                        nodes {
                            %s
                        }
                    }
                }
            }
        }
        """ % (media_fields if page == 1 else 'id', page_info, chara_fields)
        variables = dict(idIn=[media.id for media in items], page=page)

        try:
            jsonData = await anilist_api(
                dict(query=query, variables=variables), low_priority=low_priority
            )
            for mediaData in jsonData['data']['Page']['media']:
                almedia = ALMedia.model_validate(mediaData)
                media = medias_dict.pop(almedia.id)
                media.feed_page(almedia)
                found.add(media)
        except aiohttp.ClientResponseError as e:
            if e.status == 500:
                logger.exception(e)
            else:
                raise

        if len(medias_dict) > 0:
            logger.warning(f'Media.fetch_page: medias {list(medias_dict.keys())} not found')
            for m in medias_dict.values():
                del m.multitons.medias[m.id]

        return found

    @classmethod
    async def load(cls,
                   items: set['Media'],
                   full: bool = True,
                   low_priority=False,
                   _start_page: int = 1):
        complete: set[Media] = set(filter(is_complete, items))
        not_complete: set[Media] = set(filterfalse(is_complete, items))

        for m in complete:
            yield m

        for page in count(_start_page):
            if len(not_complete) == 0:
                return

            parts = list(partition_all(50, not_complete))
            logger.info(
                f"Media.load: fetching page {page} for {len(not_complete)} medias "
                f"in {len(parts)} requests")

            not_complete = set()
            for part in parts:
                fetched = await cls.fetch_page(set(part),
                                               page,
                                               low_priority=low_priority)
                for m in fetched:
                    if is_complete(m) or not full:
                        yield m
                    else:
                        not_complete.add(m)


#########
# Chara #
#########
class Chara(ALEntity[ALCharacter]):
    ALMULTITONS_KEY: str = 'charas'

    def __init__(self, multitons: ALMultitons, id_al: int) -> None:
        super().__init__(multitons, id_al)
        self.edges: list[ALMediaEdge] = []
        self.medias: set[Media] = set()
        self.staffs: set[Staff] = set()

    def feed_page(self, value: ALCharacter) -> None:
        if self.complete.is_set():
            return

        if self._aldata is None:
            self._aldata = value

        if value.media is not None:
            new_page = value.media.pageInfo.currentPage

            if new_page > self.current_page:
                self.last_pageinfo = value.media.pageInfo
                self.edges += value.media.edges

                for edge in value.media.edges:
                    media = Media.get(self.multitons, edge.node.id)
                    media.feed_page(edge.node)
                    self.medias.add(media)
                    for va in edge.voiceActors:
                        staff = Staff.get(self.multitons, va.id)
                        staff.feed_page(va)
                        self.staffs.add(staff)

                if (not value.media.pageInfo.hasNextPage or
                        len(value.media.edges) == 0):
                    self.complete.set()

    async def edgedb_merge(self, executor: AsyncIOExecutor):
        character_data = self.aldata.to_edgedb()
        medias_data = [media.aldata.to_edgedb() for media in self.medias]
        staffs_data = [staff.aldata.to_edgedb() for staff in self.staffs]
        edges_data = [
            dict(character_id=self.id,
                 media_id=edge.node.id,
                 voice_actor_ids=[va.id for va in edge.voiceActors],
                 character_role=edge.characterRole) for edge in self.edges
        ]

        logger.debug(f"Chara[{self.id}]: merging with "
                     f"{len(medias_data)} medias, {len(staffs_data)} staffs "
                     f"and {len(edges_data)} edges")
        # Narrator fix
        if self.current_page > 20:
            await edgedb_split_merge(executor, medias_data, [character_data],
                                     staffs_data, edges_data)
        else:
            await c_edge_merge_combined_by_chara(executor,
                                                 character=character_data,
                                                 medias=medias_data,
                                                 staffs=staffs_data,
                                                 edges=edges_data)

    @classmethod
    async def fetch_page(cls,
                         items: set['Chara'],
                         page: int,
                         low_priority: bool = False) -> set['Chara']:
        charas_dict = {c.id: c for c in items}
        found = set()

        query = """
        query ($idIn: [Int], $page: Int) {
            Page {
                characters(id_in: $idIn) {
                    %s
                    media(page: $page) {
                        %s
                        edges {
                            characterRole
                            node {
                                %s
                            }
                            voiceActors(language: JAPANESE) {
                                %s
                            }
                        }
                    }
                }
            }
        }
        """ % (chara_fields if page == 1 else 'id', page_info, media_fields,
               staff_fields)
        variables = dict(idIn=[chara.id for chara in items], page=page)

        try:
            jsonData = await anilist_api(
                dict(query=query, variables=variables), low_priority=low_priority
            )
            for charaData in jsonData['data']['Page']['characters']:
                alchara = ALCharacter.model_validate(charaData)
                chara = charas_dict.pop(alchara.id)
                chara.feed_page(alchara)
                found.add(chara)
        except aiohttp.ClientResponseError as e:
            if e.status == 500:
                logger.exception(e)
            else:
                raise

        if len(charas_dict) > 0:
            logger.warning(f'Chara.fetch_page: Charas {list(charas_dict.keys())} not found')
            for c in charas_dict.values():
                del c.multitons.charas[c.id]

        return found

    @classmethod
    async def load(cls,
                   items: set['Chara'],
                   full: bool = True,
                   low_priority=False,
                   _start_page: int = 1):
        complete: set[Chara] = set(filter(is_complete, items))
        not_complete: set[Chara] = set(filterfalse(is_complete, items))

        for c in complete:
            yield c

        for page in count(_start_page):
            if len(not_complete) == 0:
                return

            parts = list(partition_all(50, not_complete))
            logger.info(
                f"Chara.load: fetching page {page} for {len(not_complete)} charas "
                f"in {len(parts)} requests")

            not_complete = set()
            for part in parts:
                fetched = await cls.fetch_page(set(part),
                                               page,
                                               low_priority=low_priority)
                for c in fetched:
                    if is_complete(c) or not full:
                        yield c
                    else:
                        not_complete.add(c)


class Staff(ALEntity[ALStaff]):
    ALMULTITONS_KEY: str = 'staffs'

    def __init__(self, multitons: ALMultitons, id_al: int) -> None:
        super().__init__(multitons, id_al)
        self.edges: list[ALStaffCharacterEdge] = []
        self.medias: set[Media] = set()
        self.characters: set[Chara] = set()

    def feed_page(self, value: ALStaff) -> None:
        if self.complete.is_set():
            return

        if self._aldata is None:
            self._aldata = value

        if value.characters is not None:
            new_page = value.characters.pageInfo.currentPage

            if new_page > self.current_page:
                self.last_pageinfo = value.characters.pageInfo
                self.edges += value.characters.edges

                for edge in value.characters.edges:
                    for media_data in edge.media:
                        media = Media.get(self.multitons, media_data.id)
                        media.feed_page(media_data)
                        self.medias.add(media)
                    chara = Chara.get(self.multitons, edge.node.id)
                    chara.feed_page(edge.node)
                    self.characters.add(chara)

                if (not value.characters.pageInfo.hasNextPage or
                        len(value.characters.edges) == 0):
                    self.complete.set()

    async def edgedb_merge(self, executor: AsyncIOExecutor):
        staff_data = self.aldata.to_edgedb()
        medias_data = [media.aldata.to_edgedb() for media in self.medias]
        characters_data = [
            chara.aldata.to_edgedb() for chara in self.characters
        ]

        logger.debug(
            f"Staff[{self.id}]: merging with "
            f"{len(medias_data)} medias and {len(characters_data)} charas")
        await staff_merge_combined_medias_charas(executor,
                                                 staff=staff_data,
                                                 medias=medias_data,
                                                 characters=characters_data)

    @classmethod
    async def fetch_page(cls,
                         items: set['Staff'],
                         page: int,
                         low_priority: bool = False) -> set['Staff']:
        staffs_dict = {s.id: s for s in items}
        found = set()

        query = """
        query ($idIn: [Int], $page: Int) {
            Page {
                staff(id_in: $idIn) {
                    %s
                    characters(page: $page) {
                        %s
                        edges {
                            node {
                                %s
                            }
                            media {
                                %s
                            }
                        }
                    }
                }
            }
        }
        """ % (staff_fields if page == 1 else 'id', page_info, chara_fields,
               media_fields)
        variables = dict(idIn=[staff.id for staff in items], page=page)

        try:
            jsonData = await anilist_api(
                dict(query=query, variables=variables), low_priority=low_priority
            )
            for staffData in jsonData['data']['Page']['staff']:
                alstaff = ALStaff.model_validate(staffData)
                staff = staffs_dict.pop(alstaff.id)
                staff.feed_page(alstaff)
                found.add(staff)
        except aiohttp.ClientResponseError as e:
            if e.status == 500:
                logger.exception(e)
            else:
                raise

        if len(staffs_dict) > 0:
            logger.warning(f'Staff.fetch_page: Staffs {list(staffs_dict.keys())} not found')
            for s in staffs_dict.values():
                del s.multitons.staffs[s.id]

        return found

    @classmethod
    async def load(cls,
                   items: set['Staff'],
                   full: bool = True,
                   low_priority=False,
                   _start_page: int = 1):
        complete: set[Staff] = set(filter(is_complete, items))
        not_complete: set[Staff] = set(filterfalse(is_complete, items))

        for s in complete:
            yield s

        for page in count(_start_page):
            if len(not_complete) == 0:
                return

            parts = list(partition_all(50, not_complete))
            logger.info(
                f"Staff.load: fetching page {page} for {len(not_complete)} staffs "
                f"in {len(parts)} requests")

            not_complete = set()
            for part in parts:
                fetched = await cls.fetch_page(set(part),
                                               page,
                                               low_priority=low_priority)
                for s in fetched:
                    if is_complete(s) or not full:
                        yield s
                    else:
                        not_complete.add(s)


async def edgedb_split_merge(executor: AsyncIOExecutor, medias: list,
                             characters: list, staffs: list, edges: list):
    for part in partition_all(MERGE_COMBINED_MAX_SIZE, medias):
        await media_merge_multiple(executor, medias=part)
    for part in partition_all(MERGE_COMBINED_MAX_SIZE, characters):
        await chara_merge_multiple(executor, characters=part)
    for part in partition_all(MERGE_COMBINED_MAX_SIZE, staffs):
        await staff_merge_multiple(executor, staffs=part)
    for part in partition_all(MERGE_COMBINED_MAX_SIZE, edges):
        await c_edge_merge_multiple(executor, edges=part)


async def get_entries_df():
    entries_data = await entry_select_all(get_edgedb())
    entries = pl.DataFrame([
        dict(
            status=e.status.value,
            score=e.score,
            id_al=e.media.id_al,
            discord_id=e.account.user.discord_id,
        ) for e in entries_data
    ])
    return entries


def entries_to_scores_df(entries: pl.DataFrame) -> pl.DataFrame:
    scores = entries.pivot('discord_id', index='id_al',
                           values='score', aggregate_function='max')
    return scores


@cached(cache=TTLCache(1024, ttl=timedelta(hours=6).seconds))
async def predict_scores() -> tuple[pl.DataFrame, pl.DataFrame]:
    entries = await get_entries_df()

    # Remove PLANNING entries
    entries = entries.filter(pl.col('status') != 'PLANNING')

    # Remove users without any scored entries (null std = useless data)
    entries = entries.filter(pl.col('score').sum().over('discord_id') > 0)

    # Fill missing scores
    entries = entries.with_columns(
        pl.when(pl.col('score') > 0)
        .then(pl.col('score'))  # Nothing to do
        .when(pl.col('status') == 'CURRENT')
        .then(pl.col('score').filter(pl.col('score') > 0).quantile(0.50).over('discord_id'))
        .when(pl.col('status') == 'COMPLETED')
        .then(pl.col('score').filter(pl.col('score') > 0).quantile(0.25).over('discord_id'))
        .when(pl.col('status') == 'PAUSED')
        .then(pl.col('score').filter(pl.col('score') > 0).quantile(0.25).over('discord_id'))
        .when(pl.col('status') == 'DROPPED')
        .then(0)
        .when(pl.col('status') == 'REPEATING')
        .then(pl.col('score').filter(pl.col('score') > 0).quantile(0.75).over('discord_id'))
        .otherwise(pl.col('score'))  # Should not happen
        .alias('score')
    )

    scores = entries_to_scores_df(entries)
    scores_np = scores.select(pl.all().exclude('id_al')).to_numpy()

    # Standardize
    scaler = preprocessing.StandardScaler()
    std_scores = scaler.fit_transform(scores_np)

    # SVD
    svd = TruncatedSVD(n_components=2)
    decomp = svd.fit_transform(np.nan_to_num(std_scores))

    # Reconstruct
    p_scores_np = svd.inverse_transform(decomp)
    p_scores_np = scaler.inverse_transform(p_scores_np)
    p_scores = pl.concat(
        (scores.select('id_al'),
         pl.DataFrame(p_scores_np, schema=scores.columns[1:])),
        how='horizontal')

    return p_scores, entries
