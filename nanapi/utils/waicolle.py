import abc
import asyncio
import logging
import re
from contextlib import suppress
from datetime import date, datetime, timedelta
from functools import partial
from itertools import product
from typing import Any, Callable, Coroutine, Self, cast

import numpy as np
import numpy.typing as npt
from asyncache import cached
from cachetools import TTLCache
from cachetools.keys import hashkey
from gel import AsyncIOExecutor

from nanapi.database.anilist.anime_select_ids_upcoming import anime_select_ids_upcoming
from nanapi.database.anilist.c_edge_select_filter_media import (
    CEdgeSelectFilterMediaResultCharacter,
)
from nanapi.database.anilist.c_edge_select_filter_staff import (
    CEdgeSelectFilterStaffResultCharacter,
)
from nanapi.database.anilist.chara_select import CharaSelectResult
from nanapi.database.anilist.media_select_ids_by_season import (
    MEDIA_SELECT_IDS_BY_SEASON_SEASON,
    media_select_ids_by_season,
)
from nanapi.database.anilist.media_select_ids_by_tag import media_select_ids_by_tag
from nanapi.database.anilist.media_select_top_h import media_select_top_h
from nanapi.database.anilist.tag_select import tag_select
from nanapi.database.waicolle.medias_pool import MediasPoolResult, medias_pool
from nanapi.database.waicolle.user_pool import UserPoolResult, user_pool
from nanapi.database.waicolle.waifu_edged import WaifuEdgedResultElements
from nanapi.database.waicolle.waifu_select_by_user import WaifuSelectByUserResult
from nanapi.models.waicolle import RANKS, A, B, C, D, E, Rank, S
from nanapi.settings import TZ
from nanapi.utils.clients import get_edgedb
from nanapi.utils.redis.waicolle import daily_tag, user_daily_roll, user_weekly_roll, weekly_season

logger = logging.getLogger(__name__)

WAIFU_TYPES = WaifuEdgedResultElements | WaifuSelectByUserResult
CHARA_TYPES = (
    CharaSelectResult
    | CEdgeSelectFilterMediaResultCharacter
    | CEdgeSelectFilterStaffResultCharacter
)

RNG = np.random.default_rng()

RE_SYMBOLES = re.compile(r'[^a-zA-Z\d]+')

RATES = {S: 5, A: 15, B: 25, C: 30, D: 20, E: 5}

REROLLS_MAX_RANKS = {
    S: None,
    A: None,
    B: S,
    C: A,
    D: B,
    E: B,
}


########
# Roll #
########
class BaseRoll(abc.ABC):
    RATES: dict[Rank, int] = RATES

    def __init__(
        self, nb: int, price: int = 0, min_rank: Rank | None = None, max_rank: Rank | None = None
    ):
        self.nb = nb
        self.price = price
        self.min_rank = E if min_rank is None else min_rank
        self.max_rank = S if max_rank is None else max_rank
        self.loaded = asyncio.Event()

    async def get_name(self, executor: AsyncIOExecutor, discord_id: str) -> str:
        name = f'{self.nb} {self.max_rank.wc_rank}'
        if self.max_rank.wc_rank != self.min_rank.wc_rank:
            name += f'-{self.min_rank.wc_rank}'
        return name

    async def get_price(self, executor: AsyncIOExecutor, discord_id: str) -> int:
        return self.price

    @abc.abstractmethod
    async def load(self, executor: AsyncIOExecutor, force: bool = False):
        if force or not self.loaded.is_set():
            self.loaded.set()

    async def roll(self, executor: AsyncIOExecutor, pool_discord_id: str) -> list[int]:
        await self.loaded.wait()
        charas, probas = await self._roll(executor, pool_discord_id)
        chousen = RNG.choice(charas, size=self.nb, p=probas)
        return [int(i) for i in chousen]

    @abc.abstractmethod
    async def _roll(
        self, executor: AsyncIOExecutor, pool_discord_id: str
    ) -> tuple[npt.NDArray[np.int_], npt.NDArray[np.float64]]:
        pass

    async def _charas_probas_from_pool(
        self, pool: list[UserPoolResult] | list[MediasPoolResult]
    ) -> tuple[npt.NDArray[np.int_], npt.NDArray[np.float64]]:
        charas_ids = {
            RANKS[group.key.rank]: set(el.id_al for el in group.elements)
            for group in pool
            if (RANKS[group.key.rank] >= self.min_rank and RANKS[group.key.rank] <= self.max_rank)
        }

        chara_pool = np.full((sum(len(v) for v in charas_ids.values()),), 0)
        probas = np.zeros((len(chara_pool),))

        i = 0
        for rank, clist in charas_ids.items():
            for c in clist:
                chara_pool[i] = c
                probas[i] = self.RATES[rank] / len(charas_ids[rank])
                i += 1

        probas = probas / probas.sum()

        return chara_pool[:i], probas[:i]

    @abc.abstractmethod
    async def after(self, executor: AsyncIOExecutor, discord_id: str):
        pass

    async def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self


class EmptyPoolException(Exception):
    def __init__(self):
        super().__init__('User pool is empty')


class UserRoll(BaseRoll):
    async def load(self, executor: AsyncIOExecutor, force: bool = False):
        await super().load(executor, force=force)

    async def _roll(
        self, executor: AsyncIOExecutor, pool_discord_id: str
    ) -> tuple[npt.NDArray[np.int_], npt.NDArray[np.float64]]:
        pool = await self._cached_user_pool(executor, discord_id=pool_discord_id)
        charas, probas = await self._charas_probas_from_pool(pool)

        tot_tickets = sum(tickets for tickets in self.RATES.values())
        tickets = sum(
            tickets
            for rank, tickets in self.RATES.items()
            if rank >= self.min_rank and rank <= self.max_rank
        )
        MIN_RATE = tot_tickets / (200 * tickets)

        if len(charas) == 0 or float(np.max(probas)) > MIN_RATE:
            common_pool = await self._cached_user_pool(executor)
            common_charas, common_probas = await self._charas_probas_from_pool(common_pool)

            if len(charas) == 0:
                factor = 0
            else:
                factor = MIN_RATE / float(np.max(probas))

            logger.info(f'{pool_discord_id} pool factor: {factor} (min rate: {MIN_RATE})')
            charas = np.append(charas, common_charas)
            probas = np.append(probas * factor, common_probas * (1 - factor))

        return charas, probas

    @classmethod
    @cached(
        cache=TTLCache(1024, ttl=timedelta(hours=6).seconds),
        key=lambda *args, **kwargs: hashkey(kwargs.get('discord_id', None)),
    )
    async def _cached_user_pool(cls, executor: AsyncIOExecutor, *, discord_id: str | None = None):
        res = await user_pool(executor, discord_id=discord_id)
        if len(res) == 0:
            # do not cache empty user pool
            raise EmptyPoolException()
        return res

    async def after(self, executor: AsyncIOExecutor, discord_id: str):
        pass


class BaseMediaRoll(BaseRoll, metaclass=abc.ABCMeta):
    def __init__(
        self,
        nb: int,
        price: int = 0,
        min_rank: Rank | None = None,
        max_rank: Rank | None = None,
        genred: bool = True,
    ):
        super().__init__(nb, price, min_rank, max_rank)
        self.genred = genred
        self.ids_al: list[int] | None = None

    async def _roll(
        self, executor: AsyncIOExecutor, pool_discord_id: str | None = None
    ) -> tuple[npt.NDArray[np.int_], npt.NDArray[np.float64]]:
        pool = await self.get_pool(executor, pool_discord_id)
        return await self._charas_probas_from_pool(pool)

    async def get_pool(
        self, executor: AsyncIOExecutor, discord_id: str | None = None
    ) -> list[MediasPoolResult]:
        assert self.ids_al is not None
        ids_al = tuple(sorted(self.ids_al))
        pool = await self._cached_medias_pool(
            executor, ids_al=ids_al, discord_id=discord_id, genred=self.genred
        )
        return pool

    @classmethod
    @cached(
        cache=TTLCache(1024, ttl=timedelta(days=1).seconds),
        key=lambda *args, **kwargs: hashkey(
            kwargs.get('ids_al', None), kwargs.get('discord_id', None), kwargs.get('genred', None)
        ),
    )
    async def _cached_medias_pool(
        cls,
        executor: AsyncIOExecutor,
        *,
        ids_al: tuple[int, ...],
        discord_id: str | None = None,
        genred: bool | None = None,
    ):
        return await medias_pool(
            executor, ids_al=list(ids_al), discord_id=discord_id, genred=genred
        )


class UpcomingRoll(BaseMediaRoll):
    async def get_name(self, executor: AsyncIOExecutor, discord_id: str) -> str:
        return f'{await super().get_name(executor, discord_id)}, Upcoming anime'

    async def load(self, executor: AsyncIOExecutor, force: bool = False):
        if force or not self.loaded.is_set():
            resp = await anime_select_ids_upcoming(executor)
            self.ids_al = [media.id_al for media in resp]
            self.loaded.set()

    async def after(self, executor: AsyncIOExecutor, discord_id: str):
        pass


class HRoll(BaseMediaRoll):
    def __init__(
        self, nb: int, price: int = 0, min_rank: Rank | None = None, max_rank: Rank | None = None
    ):
        super().__init__(nb, price, min_rank, max_rank, genred=False)

    async def get_name(self, executor: AsyncIOExecutor, discord_id: str) -> str:
        return f'{await super().get_name(executor, discord_id)} (all), Top 1000 favourites H'

    async def load(self, executor: AsyncIOExecutor, force: bool = False):
        if force or not self.loaded.is_set():
            resp = await media_select_top_h(executor)
            self.ids_al = [media.id_al for media in resp]
            self.loaded.set()

    async def after(self, executor: AsyncIOExecutor, discord_id: str):
        pass


def get_current_date() -> date:
    current_time = datetime.now(tz=TZ)
    return date(current_time.year, current_time.month, current_time.day)


class TagRoll(BaseMediaRoll):
    DAILY_BASE_PRICE = 150
    DAILY_NB = 1
    daily_rolls: dict[str, Self] = {}

    def __init__(
        self,
        nb: int,
        tag: str,
        price: int = 0,
        min_rank: Rank | None = None,
        max_rank: Rank | None = None,
    ):
        super().__init__(nb, price, min_rank, max_rank, genred=False)
        self.tag = tag

    async def get_name(self, executor: AsyncIOExecutor, discord_id: str) -> str:
        pool = await self.get_pool(executor, discord_id)

        min_rank = S
        max_rank = E
        for group in pool:
            rank = RANKS[group.key.rank]
            if group.elements:
                if rank < min_rank:
                    min_rank = rank
                if rank > max_rank:
                    max_rank = rank

        return f'{self.nb} {max_rank}-{min_rank} (all), Daily tag — {self.tag}'

    async def get_price(self, executor: AsyncIOExecutor, discord_id: str) -> int:
        price = await super().get_price(executor, discord_id)

        # discount on first roll
        redis_player_key = f'{discord_id}_{get_current_date()}'
        if not await user_daily_roll.get(redis_player_key, tx=executor):
            price //= 2

        return price

    async def load(self, executor: AsyncIOExecutor, force: bool = False):
        if force or not self.loaded.is_set():
            resp = await media_select_ids_by_tag(executor, tag_name=self.tag, min_rank=60)
            self.ids_al = [media.id_al for media in resp]
            cls = self.__class__
            cls.daily_rolls[self.tag] = self
            self.loaded.set()

    async def after(self, executor: AsyncIOExecutor, discord_id: str):
        redis_player_key = f'{discord_id}_{get_current_date()}'
        await user_daily_roll.set(True, sub_key=redis_player_key)

    @classmethod
    async def get_daily(cls) -> 'TagRoll':
        today = get_current_date()
        tomorrow = today + timedelta(days=1)

        asyncio.create_task(cls.get_daily_tag(get_edgedb(), tag_date=tomorrow))

        return await cls.get_daily_tag(get_edgedb(), tag_date=today)

    @classmethod
    async def get_daily_tag(cls, executor: AsyncIOExecutor, tag_date: date) -> 'TagRoll':
        create_roll = partial(cls, nb=cls.DAILY_NB, price=cls.DAILY_BASE_PRICE)
        tag = await daily_tag.get(str(tag_date))

        if tag is not None:
            roll = cls.daily_rolls.get(tag, create_roll(tag=tag))
            await roll.load(executor)
            return roll

        yesterday = tag_date - timedelta(days=1)
        yesterday_tag = await daily_tag.get(str(yesterday))

        resp = await tag_select(executor)
        tags = [tag.name for tag in resp]
        if yesterday_tag:
            with suppress(ValueError):
                tags.remove(yesterday_tag)
        RNG.shuffle(tags)

        for tag in tags:
            roll = create_roll(tag=tag)
            await roll.load(executor, force=True)
            _, rates = await roll._roll(executor)
            if len(rates) > 400 and (1 / float(np.max(rates))) > 50:
                await daily_tag.set(tag, sub_key=str(tag_date))
                return roll

        raise RuntimeError('Could not find daily roll tag')


class SeasonalRoll(BaseMediaRoll):
    WEEKLY_BASE_PRICE = 600
    WEEKLY_NB = 5
    weekly_rolls: dict[tuple[int, MEDIA_SELECT_IDS_BY_SEASON_SEASON], 'SeasonalRoll'] = {}

    def __init__(
        self,
        nb: int,
        season_year: int,
        season: MEDIA_SELECT_IDS_BY_SEASON_SEASON,
        price: int = 0,
        min_rank: Rank | None = None,
        max_rank: Rank | None = None,
        week_key: tuple[int, int] | None = None,
    ):
        super().__init__(nb, price, min_rank, max_rank)
        self.week_key = week_key
        self.season_year = season_year
        self.season: MEDIA_SELECT_IDS_BY_SEASON_SEASON = season

    async def get_name(self, executor: AsyncIOExecutor, discord_id: str) -> str:
        pool = await self.get_pool(executor, discord_id)

        min_rank = S
        max_rank = E
        for group in pool:
            rank = RANKS[group.key.rank]
            if group.elements:
                if rank < min_rank:
                    min_rank = rank
                if rank > max_rank:
                    max_rank = rank

        return (
            f'{self.nb} {max_rank}-{min_rank}, '
            f'Weekly Seasonal — {self.season.capitalize()} {self.season_year}'
        )

    async def get_price(self, executor: AsyncIOExecutor, discord_id: str) -> int:
        price = await super().get_price(executor, discord_id)

        # discount on first roll
        curr_date = get_current_date().isocalendar()
        redis_player_key = f'{discord_id}_{(curr_date.year, curr_date.week)}'
        if not await user_weekly_roll.get(redis_player_key, tx=executor):
            price //= 2

        return price

    async def load(self, executor: AsyncIOExecutor, force: bool = False) -> None:
        if force or not self.loaded.is_set():
            resp = await media_select_ids_by_season(
                executor,
                season_year=self.season_year,
                season=self.season,
            )
            self.ids_al = [media.id_al for media in resp]
            cls = self.__class__
            cls.weekly_rolls[self.season_year, self.season] = self
            self.loaded.set()

    async def after(self, executor: AsyncIOExecutor, discord_id: str):
        curr_date = get_current_date().isocalendar()
        redis_player_key = f'{discord_id}_{(curr_date.year, curr_date.week)}'
        await user_weekly_roll.set(True, sub_key=redis_player_key)

    @classmethod
    async def get_weekly(cls) -> 'SeasonalRoll':
        today = get_current_date()
        today_iso = today.isocalendar()
        week_key = (today_iso.year, today_iso.week)

        next_week = today + timedelta(weeks=1)
        next_week_iso = next_week.isocalendar()
        next_week_key = next_week.year, next_week_iso.week

        asyncio.create_task(cls.get_weekly_season(get_edgedb(), week_key=next_week_key))

        return await cls.get_weekly_season(get_edgedb(), week_key)

    @classmethod
    async def get_weekly_season(
        cls, executor: AsyncIOExecutor, week_key: tuple[int, int]
    ) -> 'SeasonalRoll':
        create_roll = partial(cls, nb=cls.WEEKLY_NB, price=cls.WEEKLY_BASE_PRICE)
        saved = await weekly_season.get(str(week_key))
        if saved:
            year_str, season_str = saved.split('_')
            year, season = int(year_str), cast(MEDIA_SELECT_IDS_BY_SEASON_SEASON, season_str)
            key = year, season

            roll = cls.weekly_rolls.get(key, create_roll(season_year=year, season=season))
            await roll.load(executor)
            return roll

        roll_year, roll_week = week_key
        last_week_key = (roll_year, roll_week - 1) if roll_week > 1 else (roll_year - 1, 52)
        last_week_season_saved = await weekly_season.get(str(last_week_key))

        # boomer and zoomer enough ig
        current_year = datetime.now().year
        seasons = cast(
            list[tuple[int, MEDIA_SELECT_IDS_BY_SEASON_SEASON]],
            list(product(range(1990, current_year + 1), ['WINTER', 'SPRING', 'SUMMER', 'FALL'])),
        )

        if last_week_season_saved:
            last_week_year, last_week_season = last_week_season_saved.split('_')
            with suppress(ValueError):
                seasons.remove(
                    (
                        int(last_week_year),
                        cast(MEDIA_SELECT_IDS_BY_SEASON_SEASON, last_week_season),
                    )
                )

        RNG.shuffle(seasons)

        for year_str, season_str in seasons:
            roll = create_roll(season_year=year_str, season=season_str)
            await roll.load(executor, force=True)
            _, rates = await roll._roll(executor)
            if len(rates) > 400 and (1 / float(np.max(rates))) > 50:
                await weekly_season.set(f'{year_str}_{season_str}', sub_key=str(week_key))
                return roll

        raise RuntimeError('Could not find weekly roll season')


ROLLS: dict[str, Callable[[], Coroutine[None, None, BaseRoll]]] = {
    'A': UserRoll(price=250, nb=5, max_rank=E),
    'B': UserRoll(price=75, nb=1, max_rank=C),
    'C': UserRoll(price=300, nb=5, max_rank=C),
    'D': UserRoll(price=150, nb=1),
    'E': UserRoll(price=400, nb=3),
    'F': UserRoll(price=600, nb=5),
    'G': UpcomingRoll(price=600, nb=5),
    'H': HRoll(price=69, nb=1),
    'daily': TagRoll.get_daily,
    'weekly': SeasonalRoll.get_weekly,
}


async def get_roll(roll_id: str) -> BaseRoll | None:
    roll = ROLLS.get(roll_id)
    if roll is None:
        return None

    return await roll()


async def load_rolls():
    rolls = {roll_id: await roll_getter() for roll_id, roll_getter in ROLLS.items()}
    await asyncio.gather(*[roll.load(get_edgedb()) for roll in rolls.values()])
    return rolls
