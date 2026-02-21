import abc
import asyncio
import logging
import re
from contextlib import suppress
from datetime import date, datetime, timedelta
from itertools import product
from typing import Any, Callable, Self, cast

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

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self


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
        return await user_pool(executor, discord_id=discord_id)

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
    daily_rolls: dict[date, Self] = {}

    def __init__(
        self,
        nb: int,
        price: int = 0,
        min_rank: Rank | None = None,
        max_rank: Rank | None = None,
        forced_tag: str | None = None,
        tag_date: date | None = None,
        discount_first: bool = False,
    ):
        super().__init__(nb, price, min_rank, max_rank, genred=False)
        self.tag_date = tag_date
        self.tag = forced_tag
        self.discount_first = discount_first

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
        if self.discount_first:
            redis_player_key = f'{discord_id}_{get_current_date()}'
            if not await user_daily_roll.get(redis_player_key, tx=executor):
                price //= 2
        return price

    async def load(self, executor: AsyncIOExecutor, force: bool = False):
        if force or not self.loaded.is_set():
            if not self.tag:
                if not self.tag_date:
                    raise Exception('TagRoll must have a tag or a tag_date')
                self.tag = await self.get_daily_tag(executor, self.tag_date)

            resp = await media_select_ids_by_tag(executor, tag_name=self.tag, min_rank=60)
            self.ids_al = [media.id_al for media in resp]
            self.loaded.set()

    async def after(self, executor: AsyncIOExecutor, discord_id: str):
        if self.discount_first:
            redis_player_key = f'{discord_id}_{get_current_date()}'
            await user_daily_roll.set(True, sub_key=redis_player_key)

    @classmethod
    def get_daily(cls) -> Self:
        today = get_current_date()
        if today not in cls.daily_rolls:
            cls.daily_rolls[today] = cls(
                price=cls.DAILY_BASE_PRICE, nb=cls.DAILY_NB, tag_date=today, discount_first=True
            )
        tomorrow = today + timedelta(days=1)
        if tomorrow not in cls.daily_rolls:
            cls.daily_rolls[tomorrow] = cls(
                price=cls.DAILY_BASE_PRICE, nb=cls.DAILY_NB, tag_date=tomorrow, discount_first=True
            )
            asyncio.create_task(cls.daily_rolls[tomorrow].load(get_edgedb(), force=True))
        return cls.daily_rolls[today]

    @staticmethod
    async def get_daily_tag(executor: AsyncIOExecutor, tag_date: date) -> str:
        tag = await daily_tag.get(str(tag_date))

        if tag is not None:
            return tag

        yesterday = tag_date - timedelta(days=1)
        yesterday_tag = await daily_tag.get(str(yesterday))

        resp = await tag_select(executor)
        tags = [tag.name for tag in resp]
        if yesterday_tag:
            with suppress(ValueError):
                tags.remove(yesterday_tag)
        RNG.shuffle(tags)

        for tag in tags:
            roll = TagRoll(1, forced_tag=tag)
            await roll.load(executor, force=True)
            _, rates = await roll._roll(executor)
            if len(rates) > 400 and (1 / float(np.max(rates))) > 50:
                await daily_tag.set(tag, sub_key=str(tag_date))
                return tag

        raise RuntimeError('Could not find daily roll tag')


class SeasonalRoll(BaseMediaRoll):
    WEEKLY_BASE_PRICE = 600
    WEEKLY_NB = 5
    weekly_rolls: dict[tuple[int, int], Self] = {}

    def __init__(
        self,
        nb: int,
        price: int = 0,
        min_rank: Rank | None = None,
        max_rank: Rank | None = None,
        week_key: tuple[int, int] | None = None,
        season_year: int | None = None,
        season: MEDIA_SELECT_IDS_BY_SEASON_SEASON | None = None,
        discount_first: bool = False,
    ):
        super().__init__(nb, price, min_rank, max_rank)
        self.week_key = week_key
        self.season_year = season_year
        self.season: MEDIA_SELECT_IDS_BY_SEASON_SEASON | None = season
        self.discount_first = discount_first

    async def get_name(self, executor: AsyncIOExecutor, discord_id: str) -> str:
        assert self.season_year
        assert self.season

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
        if self.discount_first:
            curr_date = get_current_date().isocalendar()
            redis_player_key = f'{discord_id}_{(curr_date.year, curr_date.week)}'
            if not await user_weekly_roll.get(redis_player_key, tx=executor):
                price //= 2
        return price

    async def load(self, executor: AsyncIOExecutor, force: bool = False):
        if force or not self.loaded.is_set():
            if not self.season_year or not self.season:
                if not self.week_key:
                    raise Exception('SeasonalRoll must have a season or a week_key')
                self.season_year, self.season = await self.get_weekly_season(
                    executor, self.week_key
                )

            resp = await media_select_ids_by_season(
                executor,
                season_year=self.season_year,
                season=self.season,
            )
            self.ids_al = [media.id_al for media in resp]
            self.loaded.set()

    async def after(self, executor: AsyncIOExecutor, discord_id: str):
        if self.discount_first:
            curr_date = get_current_date().isocalendar()
            redis_player_key = f'{discord_id}_{(curr_date.year, curr_date.week)}'
            await user_weekly_roll.set(True, sub_key=redis_player_key)

    @classmethod
    def get_weekly(cls) -> Self:
        today = get_current_date()
        today_iso = today.isocalendar()
        week_key = (today_iso.year, today_iso.week)
        if week_key not in cls.weekly_rolls:
            cls.weekly_rolls[week_key] = cls(
                price=cls.WEEKLY_BASE_PRICE,
                nb=cls.WEEKLY_NB,
                week_key=week_key,
                discount_first=True,
            )
        next_week_key = (
            (today_iso.year, today_iso.week + 1)
            if today_iso.week < 52
            else (today_iso.year + 1, 1)
        )
        if next_week_key not in cls.weekly_rolls:
            cls.weekly_rolls[next_week_key] = cls(
                price=cls.WEEKLY_BASE_PRICE,
                nb=cls.WEEKLY_NB,
                week_key=next_week_key,
                discount_first=True,
            )
            asyncio.create_task(cls.weekly_rolls[next_week_key].load(get_edgedb(), force=True))
        return cls.weekly_rolls[week_key]

    @staticmethod
    async def get_weekly_season(
        executor: AsyncIOExecutor, week_key: tuple[int, int]
    ) -> tuple[int, MEDIA_SELECT_IDS_BY_SEASON_SEASON]:
        saved = await weekly_season.get(str(week_key))
        if saved:
            year, season = saved.split('_')
            return (int(year), cast(MEDIA_SELECT_IDS_BY_SEASON_SEASON, season))

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

        for year, season in seasons:
            roll = SeasonalRoll(1, season_year=year, season=season)
            await roll.load(executor, force=True)
            _, rates = await roll._roll(executor)
            if len(rates) > 400 and (1 / float(np.max(rates))) > 50:
                await weekly_season.set(f'{year}_{season}', sub_key=str(week_key))
                return year, season

        raise RuntimeError('Could not find weekly roll season')


ROLLS: dict[str, Callable[[], BaseRoll]] = {
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
