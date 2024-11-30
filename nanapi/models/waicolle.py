from dataclasses import dataclass
from enum import Enum
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel

from nanapi.database.anilist.media_select import MediaSelectResult
from nanapi.database.anilist.staff_select import StaffSelectResult
from nanapi.database.waicolle.collection_get_by_id import CollectionGetByIdResult
from nanapi.database.waicolle.player_merge import PLAYER_MERGE_GAME_MODE
from nanapi.database.waicolle.player_select_all import PlayerSelectAllResult
from nanapi.database.waicolle.user_pool import WaicolleRank
from nanapi.database.waicolle.waifu_replace_custom_position import (
    WAIFU_REPLACE_CUSTOM_POSITION_CUSTOM_POSITION,
)
from nanapi.database.waicolle.waifu_select import WaifuSelectResult


########
# Rank #
########
@dataclass
class Rank:
    tier: int
    wc_rank: str
    min_favourites: int  # included
    blood_shards: int
    blood_price: int
    color: int
    emoji: str

    def __gt__(self, other: Self):
        return self.tier < other.tier

    def __ge__(self, other: Self):
        return self.tier <= other.tier

    def __lt__(self, other: Self):
        return self.tier > other.tier

    def __le__(self, other: Self):
        return self.tier >= other.tier

    def __eq__(self, other: object):
        return isinstance(other, self.__class__) and self.tier == other.tier

    def __hash__(self):
        return self.tier

    def __str__(self) -> str:
        return self.wc_rank


S = Rank(
    tier=1,
    wc_rank=WaicolleRank.S,
    min_favourites=3000,
    blood_shards=3000,
    blood_price=12000,
    color=0xF1C40F,
    emoji='🟨',
)
A = Rank(
    tier=2,
    wc_rank=WaicolleRank.A,
    min_favourites=1000,
    blood_shards=1000,
    blood_price=3000,
    color=0x1ABC9C,
    emoji='🟩',
)
B = Rank(
    tier=3,
    wc_rank=WaicolleRank.B,
    min_favourites=200,
    blood_shards=400,
    blood_price=1000,
    color=0x7289DA,
    emoji='🟦',
)
C = Rank(
    tier=4,
    wc_rank=WaicolleRank.C,
    min_favourites=20,
    blood_shards=200,
    blood_price=400,
    color=0x9B59B6,
    emoji='🟪',
)
D = Rank(
    tier=5,
    wc_rank=WaicolleRank.D,
    min_favourites=1,
    blood_shards=150,
    blood_price=300,
    color=0x99AAB5,
    emoji='⬜',
)
E = Rank(
    tier=6,
    wc_rank=WaicolleRank.E,
    min_favourites=0,
    blood_shards=150,
    blood_price=300,
    color=0,
    emoji='⬛',
)

RANKS: dict[str, Rank] = {
    WaicolleRank.S: S,
    WaicolleRank.A: A,
    WaicolleRank.B: B,
    WaicolleRank.C: C,
    WaicolleRank.D: D,
    WaicolleRank.E: E,
}


###########
# FastAPI #
###########
class UpsertPlayerBody(BaseModel):
    discord_username: str
    game_mode: PLAYER_MERGE_GAME_MODE


class AddPlayerCoinsBody(BaseModel):
    moecoins: int | None = None
    blood_shards: int | None = None


class DonatePlayerCoinsBody(BaseModel):
    moecoins: int


class NewCollectionBody(BaseModel):
    discord_id: int
    name: str


class RollData(BaseModel):
    id: str
    name: str
    price: int


class PlayerSelectResult(PlayerSelectAllResult):
    pass


class CollageResult(BaseModel):
    url: str | None = None
    total: int


class MediaAlbumResult(CollageResult):
    owned: int
    media: MediaSelectResult


class StaffAlbumResult(CollageResult):
    owned: int
    staff: StaffSelectResult


class CollectionAlbumResult(CollageResult):
    owned: int
    collection: CollectionGetByIdResult


class CollageChoice(str, Enum):
    FULL = 'FULL'
    LOCKED = 'LOCKED'
    UNLOCKED = 'UNLOCKED'
    ASCENDED = 'ASCENDED'
    EDGED = 'EDGED'
    CUSTOM = 'CUSTOM'


COLLAGE_CHOICE = Literal['FULL', 'LOCKED', 'UNLOCKED', 'ASCENDED', 'EDGED', 'CUSTOM']


class BulkUpdateWaifusBody(BaseModel):
    locked: bool | None = None
    blooded: bool | None = None
    nanaed: bool | None = None
    custom_collage: bool | None = None


class NewTradeBody(BaseModel):
    author_discord_id: int
    received_ids: list[UUID]
    offeree_discord_id: int
    offered_ids: list[UUID]
    blood_shards: int | None = None


class CommitTradeResponse(BaseModel):
    received: list[WaifuSelectResult]
    offered: list[WaifuSelectResult]


class RerollBody(BaseModel):
    player_discord_id: int
    waifus_ids: list[UUID]
    bot_discord_id: int


class RerollResponse(BaseModel):
    obtained: list[WaifuSelectResult]
    nanascends: list[WaifuSelectResult]


class CollectionNameAutocompleteResult(BaseModel):
    id: UUID
    name: str
    author_discord_id: int


class NewOfferingBody(BaseModel):
    player_discord_id: int
    chara_id_al: int
    bot_discord_id: int


class NewFrozenAutotradeBody(BaseModel):
    player_discord_id: int
    chara_id_al: int


class NewCouponBody(BaseModel):
    code: str | None = None


class CustomizeWaifuBody(BaseModel):
    custom_image: str | None = None
    custom_name: str | None = None


class ReorderWaifuBody(BaseModel):
    custom_position: WAIFU_REPLACE_CUSTOM_POSITION_CUSTOM_POSITION | None = None
    other_waifu_id: UUID | None = None


class PlayerTrackReversedResult(BaseModel):
    waifu: WaifuSelectResult
    trackers_not_owners: list[PlayerSelectResult]
    locked: list[WaifuSelectResult]
