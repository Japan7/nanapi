import asyncio
import logging
import time
from dataclasses import dataclass
from functools import partial
from itertools import batched, chain, count
from typing import Any, TypeVar, final, override

import aiohttp
import orjson
from pydantic import BaseModel

import nanapi.settings as settings
from nanapi.database.anilist.chara_merge_multiple import chara_merge_multiple
from nanapi.database.anilist.chara_select_all_ids import chara_select_all_ids
from nanapi.database.anilist.media_merge_multiple import media_merge_multiple
from nanapi.database.anilist.media_select_all_ids import (
    MediaSelectAllIdsResult,
    media_select_all_ids,
)
from nanapi.database.anilist.staff_merge_multiple import staff_merge_multiple
from nanapi.database.anilist.staff_select_all_ids import staff_select_all_ids
from nanapi.models.anilist import (
    ALBaseModel,
    ALCharacter,
    ALListEntry,
    ALMedia,
    ALStaff,
    AnilistService,
    MALListResp,
    MALListRespDataEntry,
    MediaTag,
    MediaType,
)
from nanapi.settings import MAL_CLIENT_ID
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

media_fields = (
    """
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
"""
    % base_fields
)

chara_fields = (
    """
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
"""
    % base_fields
)

staff_fields = (
    """
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
"""
    % base_fields
)

tag_fields = """
id
name
description
category
isAdult
"""


@final
class ALRateLimit(Exception):
    def __init__(self, reset_at: int):
        super().__init__(f'Rate limited until {reset_at}')
        self.reset_at = reset_at

    @property
    def reset_in(self):
        return self.reset_at - time.time()


@final
class ALAPI:
    RATE_LIMIT = 90

    def __init__(self, low_priority_thresh: int = settings.AL_LOW_PRIORITY_THRESH) -> None:
        self.low_priority_ready = asyncio.Event()
        self.low_priority_ready.set()
        self.reset_task: asyncio.Task[None] | None = None
        self._reset_at: int = 0
        self.last_request_time = 0
        self._remaining = ALAPI.RATE_LIMIT
        # NOTE: just so low priority tasks don't overshoot the threshold too much
        self.low_priority_semaphore = asyncio.Semaphore(2)
        self.low_priority_thresh = low_priority_thresh

    async def reset(self):
        loop = asyncio.get_running_loop()
        while self.last_request_time + 60 > loop.time():
            wait_time = (self.last_request_time + 60) - loop.time()
            logger.debug(f'ALAPI reset: sleeping for {wait_time:.2f}s')
            await asyncio.sleep(wait_time)

        self.remaining = ALAPI.RATE_LIMIT

    @property
    def reset_at(self):
        return self._reset_at

    @reset_at.setter
    def reset_at(self, value: int):
        self._reset_at = value + 1

    @property
    def reset_in(self):
        normal_reset_in = self.reset_at - time.time()
        if normal_reset_in >= 0:
            return normal_reset_in

        # it's odd and I'd rather be safe in that case
        return max(self.last_request_time + 60 - time.time(), 1)

    @reset_in.setter
    def reset_in(self, value: int):
        self._reset_at = int(time.time()) + value

    @property
    def remaining(self):
        return self._remaining

    @remaining.setter
    def remaining(self, value: int):
        logger.debug(f'ALAPI rate limit: {value} remaining requests')
        self._remaining = value
        if value > self.low_priority_thresh:
            self.low_priority_ready.set()
        else:
            self.low_priority_ready.clear()

        loop = asyncio.get_running_loop()
        self.last_request_time = int(loop.time())
        if self.reset_task is None or self.reset_task.done():
            self.reset_task = asyncio.create_task(self.reset())

    async def _call[T: BaseModel](
        self,
        json_query: bytes,
        model: type[T],
        raise_rate_limit: bool = False,
        timeout: aiohttp.ClientTimeout | None = None,
    ) -> T:
        while True:
            try:
                if self.reset_at > time.time():
                    raise ALRateLimit(self.reset_at)

                headers = {'Content-Type': 'application/json'}
                async with get_session().post(
                    AL_URL, timeout=timeout, data=json_query, headers=headers
                ) as resp:
                    if 'X-RateLimit-Remaining' in resp.headers:
                        self.remaining = int(resp.headers['X-RateLimit-Remaining'])
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
                        json_data: dict[str, Any] = orjson.loads(raw_resp)
                    except Exception:
                        logger.error(await resp.text())
                        raise

                    if 'errors' in json_data:
                        raise RuntimeError(str(json_data['errors']))

                    return model.model_validate(json_data)
            except ALRateLimit:
                if raise_rate_limit:
                    raise
                else:
                    logger.debug(f'ALAPI rate limit: reached, sleep for {self.reset_in:.2f}s')
                    await asyncio.sleep(self.reset_in)

    @default_backoff
    async def __call__[T: BaseModel](
        self,
        json: dict[str, Any],
        *,
        model: type[T],
        raise_rate_limit: bool = False,
        timeout: aiohttp.ClientTimeout | None = None,
    ) -> T:
        json_query = orjson.dumps(json)

        logger.debug(f'ALAPI call: {model=}')

        request = partial(
            self._call,
            json_query=json_query,
            raise_rate_limit=raise_rate_limit,
            timeout=timeout,
            model=model,
        )

        if self.low_priority_thresh > 0:
            async with self.low_priority_semaphore:
                _ = await self.low_priority_ready.wait()
                return await request()
        else:
            return await request()

    def timeout_anilist_loader(self):
        if reset_at := self.reset_at:
            reset_in = reset_at - time.time()
            if reset_in > JOB_TIMEOUT:
                return reset_in

        return JOB_TIMEOUT


anilist_api = ALAPI()


def al_set_high_priority():
    anilist_api.low_priority_thresh = 0


class MALMapper(dict[MediaType, dict[int, int]]):
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


@dataclass(frozen=True)
class ListEntry:
    id_al: int
    status: str
    progress: int
    score: float


class EntryList(BaseModel):
    entries: list[ALListEntry]


class MediaListsCollection(BaseModel):
    lists: list[EntryList]


class MediaListCollectionData(BaseModel):
    MediaListCollection: MediaListsCollection


class ALEntriesResponse(BaseModel):
    data: MediaListCollectionData


class Userlist:
    service: AnilistService

    def __init__(self, username: str):
        self.username: str = username

    async def refresh(
        self,
        media_type: MediaType,
    ) -> list[ListEntry]:
        return []

    def to_edgedb(self, media_type: MediaType, entries: list[ListEntry]) -> dict[str, Any]:
        edgedb_data = dict(
            service=self.service.value,
            username=self.username,
            type=media_type.value,
            entries=list(entries),
        )
        return edgedb_data

    @override
    def __str__(self):
        return f'<{self.__class__.__name__} {self.username=}>'

    __repr__ = __str__


@final
class ALUserlist(Userlist):
    service = AnilistService.ANILIST

    @override
    async def refresh(self, media_type: MediaType) -> list[ListEntry]:
        # fetch updated list
        entries = await self.fetch_entries(media_type)

        user_entries: list[ListEntry] = []
        for entry in entries.values():
            user_entries.append(
                ListEntry(
                    id_al=entry.media.id,
                    status=entry.status,
                    progress=entry.progress,
                    score=entry.score,
                )
            )

        return user_entries

    async def fetch_entries(self, media_type: MediaType) -> dict[int, ALListEntry]:
        query = """
        query ($username: String, $type: MediaType) {
            MediaListCollection(userName: $username, type: $type) {
                lists {
                    entries {
                        score(format: POINT_10_DECIMAL)
                        status
                        progress
                        media {
                            id
                        }
                    }
                }
            }
        }
        """
        variables = {
            'username': self.username,
            'type': media_type,
        }

        jsonData = await anilist_api(
            {'query': query, 'variables': variables},
            model=ALEntriesResponse,
            timeout=aiohttp.ClientTimeout(total=300),
        )

        entries = chain.from_iterable(l.entries for l in jsonData.data.MediaListCollection.lists)

        # deduplicate entries in case the media is in several lists
        return {entry.media.id: entry for entry in entries}

    @override
    def __str__(self):
        return f'https://anilist.co/user/{self.username}'


class MediaPage(BaseModel):
    media: list[ALMedia]


class MediaData(BaseModel):
    Page: MediaPage


class ALMediaResponse(BaseModel):
    data: MediaData


@final
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

    @override
    async def refresh(self, media_type: MediaType) -> list[ListEntry]:
        for _ in range(3):
            try:
                userlist = await self.fetch_list(self.username, media_type)
                break
            except Exception as e:
                logger.error(e)
                await asyncio.sleep(1)
        else:
            logger.error(f'MALUserlist: refresh failed for {self.username}')
            return []

        al_ids = await self.get_al_ids(media_type, set(entry.node.id for entry in userlist))

        user_entries: list[ListEntry] = []
        for entry in userlist:
            repeating = (
                entry.list_status.is_rewatching
                if media_type == MediaType.ANIME
                else entry.list_status.is_rereading
            )
            status = 'REPEATING' if repeating else self.MAL_STATUS[entry.list_status.status]

            progress = (
                entry.list_status.num_episodes_watched
                if media_type is MediaType.ANIME
                else entry.list_status.num_chapters_read
            )

            if id_al := al_ids.get(entry.node.id, None):
                user_entries.append(
                    ListEntry(
                        id_al=id_al,
                        status=status,
                        progress=progress or 0,  # FIXME: can be None?
                        score=entry.list_status.score,
                    )
                )

        return user_entries

    @classmethod
    async def fetch_list(cls, username: str, media_type: MediaType):
        async with cls.refresh_lock:
            url = f'https://api.myanimelist.net/v2/users/{username}/{media_type.lower()}list'
            headers = {'X-MAL-CLIENT-ID': MAL_CLIENT_ID}
            entries: list[MALListRespDataEntry] = []
            for offset in count(0, 1000):
                params = dict(limit=1000, offset=offset, fields='list_status')
                async with get_session().get(url, params=params, headers=headers) as resp:
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
    async def get_al_ids(cls, media_type: MediaType, ids_mal: set[int]) -> dict[int, int | None]:
        to_fetch = [id_mal for id_mal in ids_mal if id_mal not in malmapper[media_type]]

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
            for sub_to_fetch in batched(to_fetch, 50):
                variables = {
                    'idMal_in': sub_to_fetch,
                    'type': media_type,
                }
                try:
                    jsonData = await anilist_api(
                        {'query': query, 'variables': variables},
                        model=ALMediaResponse,
                    )
                    for almedia in jsonData.data.Page.media:
                        assert almedia.idMal is not None
                        malmapper[media_type][almedia.idMal] = almedia.id
                except aiohttp.ClientResponseError as e:
                    if e.status == 404:
                        msg = f'MAL ids {ids_mal} not found on AniList'
                        logger.info(msg)
                    else:
                        raise

        return {id_mal: malmapper[media_type].get(id_mal, None) for id_mal in ids_mal}

    @override
    def __str__(self):
        return f'https://myanimelist.net/profile/{self.username}'


SERVICE_USER_LIST: dict[AnilistService, type[Userlist]] = {
    AnilistService.ANILIST: ALUserlist,
    AnilistService.MYANIMELIST: MALUserlist,
}


class ALTagData(BaseModel):
    MediaTagCollection: list[MediaTag]


class ALTagResponse(BaseModel):
    data: ALTagData


async def get_tags() -> list[MediaTag]:
    query = (
        """
    query {
        MediaTagCollection {
            %s
        }
    }
    """
        % tag_fields
    )
    jsonData = await anilist_api(dict(query=query), model=ALTagResponse)
    return jsonData.data.MediaTagCollection


merge_lock = asyncio.Lock()

T = TypeVar('T', bound=ALBaseModel)


async def fetch_media(*media_ids: int, page: int = 1) -> list[ALMedia]:
    if len(media_ids) == 0:
        return []

    query = """
    query ($idIn: [Int], $page: Int) {
        Page {
            media(id_in: $idIn) {
                %s
                characters(page: $page) {
                    %s
                    nodes {
                        id
                    }
                }
            }
        }
    }
    """ % (media_fields if page == 1 else 'id', page_info)
    medias: list[ALMedia] = []

    for mbatch in batched(media_ids, 50):
        not_found = set(mbatch)
        try:
            variables = dict(idIn=mbatch, page=page)
            jsonData = await anilist_api(
                dict(query=query, variables=variables),
                model=ALMediaResponse,
            )
            for almedia in jsonData.data.Page.media:
                not_found.remove(almedia.id)
                medias.append(almedia)
        except aiohttp.ClientResponseError as e:
            if e.status == 500:
                logger.exception(e)
            else:
                raise

        if len(not_found) > 0:
            logger.warning(f'fetch_media: medias {not_found} not found')

    return medias


class ALCharaPage(BaseModel):
    characters: list[ALCharacter]


class ALCharaData(BaseModel):
    Page: ALCharaPage


class ALCharaResponse(BaseModel):
    data: ALCharaData


async def fetch_chara(*charas_ids: int, page: int = 1) -> list[ALCharacter]:
    if len(charas_ids) == 0:
        return []

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
                            id
                        }
                        voiceActors(language: JAPANESE) {
                            id
                            favourites
                        }
                    }
                }
            }
        }
    }
    """ % (chara_fields if page == 1 else 'id', page_info)

    charas: list[ALCharacter] = []

    for cbatch in batched(charas_ids, 50):
        not_found = set(cbatch)

        try:
            variables = dict(idIn=cbatch, page=page)
            jsonData = await anilist_api(
                dict(query=query, variables=variables),
                model=ALCharaResponse,
            )
            for alchara in jsonData.data.Page.characters:
                not_found.remove(alchara.id)
                charas.append(alchara)
        except aiohttp.ClientResponseError as e:
            if e.status == 500:
                logger.exception(e)
            else:
                raise

        if len(not_found) > 0:
            logger.warning(f'fetch_chara: Charas {not_found} not found')

    return charas


class ALStaffPage(BaseModel):
    staff: list[ALStaff]


class ALStaffData(BaseModel):
    Page: ALStaffPage


class ALStaffResponse(BaseModel):
    data: ALStaffData


async def fetch_staff(*staff_ids: int, page: int = 1) -> list[ALStaff]:
    if len(staff_ids) == 0:
        return []

    query = """
    query ($idIn: [Int], $page: Int) {
        Page {
            staff(id_in: $idIn) {
                %s
                characters(page: $page) {
                    %s
                    nodes {
                        id
                    }
                }
            }
        }
    }
    """ % (staff_fields if page == 1 else 'id', page_info)
    staffs: list[ALStaff] = []

    for sbatch in batched(staff_ids, 50):
        not_found = set(sbatch)
        try:
            variables = dict(idIn=sbatch, page=page)
            jsonData = await anilist_api(
                dict(query=query, variables=variables),
                model=ALStaffResponse,
            )
            for alstaff in jsonData.data.Page.staff:
                not_found.remove(alstaff.id)
                staffs.append(alstaff)
        except aiohttp.ClientResponseError as e:
            if e.status == 500:
                logger.exception(e)
            else:
                raise

        if len(not_found) > 0:
            logger.warning(f'fetch_staff: Staffs {not_found} not found')

    return staffs


async def update_missing_media(media_ids: set[int]) -> None:
    all_ids = await media_select_all_ids(get_edgedb())
    ids_db = {i.id_al for i in all_ids}

    ids = media_ids - ids_db
    if len(ids) == 0:
        return

    batches = list(batched(ids, 50))
    logger.info(f'updating {len(ids)} medias in {len(batches)} requests')

    for mbatch in batches:
        medias = await fetch_media(*mbatch)
        _ = await media_merge_multiple(
            get_edgedb(), medias=[media.to_edgedb() for media in medias]
        )


async def update_missing_characters(charas_ids: set[int]) -> None:
    all_ids = await chara_select_all_ids(get_edgedb())
    ids_db = {i.id_al for i in all_ids}

    ids = charas_ids - ids_db
    if len(ids) == 0:
        return
    batches = list(batched(ids, 50))
    logger.info(f'updating {len(ids)} charas in {len(batches)} requests')

    for cbatch in batches:
        charas = await fetch_chara(*cbatch)
        _ = await chara_merge_multiple(
            get_edgedb(), characters=[chara.to_edgedb() for chara in charas]
        )


async def update_missing_staff(staff_ids: set[int]) -> None:
    all_ids = await staff_select_all_ids(get_edgedb())
    ids_db = {i.id_al for i in all_ids}

    ids = staff_ids - ids_db
    if len(ids) == 0:
        return

    batches = list(batched(ids, 50))
    logger.info(f'updating {len(ids)} staffs in {len(batches)} requests')

    for sbatch in batches:
        staff = await fetch_staff(*sbatch)
        _ = await staff_merge_multiple(get_edgedb(), staffs=[s.to_edgedb() for s in staff])
