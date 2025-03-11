import re
from enum import Enum
from typing import Any, Literal, override

from pydantic import BaseModel

from nanapi.database.anilist.account_merge import ACCOUNT_MERGE_SERVICE
from nanapi.database.waicolle.user_pool import WaicolleRank
from nanapi.models.waicolle import RANKS


##################
# AniList models #
##################
class AnilistService(str, Enum):
    ANILIST = 'ANILIST'
    MYANIMELIST = 'MYANIMELIST'


ANILIST_SERVICES = Literal['ANILIST', 'MYANIMELIST']


class MediaType(str, Enum):
    ANIME = 'ANIME'
    MANGA = 'MANGA'


MEDIA_TYPES = Literal['ANIME', 'MANGA']


class MediaTag(BaseModel):
    id: int
    rank: int | None = None
    name: str | None = None
    description: str | None = None
    category: str | None = None
    isAdult: bool | None = None

    def to_edgedb(self):
        data = dict(
            id_al=self.id,
            rank=self.rank,
            name=self.name,
            description=self.description,
            category=self.category,
            is_adult=self.isAdult,
        )
        return data


class ALPageInfo(BaseModel):
    currentPage: int
    hasNextPage: bool


class ALBaseModel(BaseModel):
    id: int
    favourites: int | None = None
    siteUrl: str | None = None

    def to_edgedb(self) -> dict[str, Any]:
        data = dict(id_al=self.id, favourites=self.favourites, site_url=self.siteUrl)
        return data

    @override
    def __hash__(self):
        return hash(self.id)


class ALMediaTitle(BaseModel):
    userPreferred: str
    english: str | None = None
    native: str | None = None


class ALMediaCoverImage(BaseModel):
    extraLarge: str
    color: str | None = None


class ALCharacterNode(BaseModel):
    id: int


class ALStaffName(BaseModel):
    userPreferred: str
    alternative: list[str] | None = None
    native: str | None = None


class ALStaffImage(BaseModel):
    large: str


class ALStaffDate(BaseModel):
    year: int | None = None
    month: int | None = None
    day: int | None = None


class ALCharacterID(BaseModel):
    id: int


class ALStaffCharacterConnection(BaseModel):
    pageInfo: ALPageInfo
    nodes: list[ALCharacterID]


class ALStaff(ALBaseModel):
    id: int
    characters: ALStaffCharacterConnection
    name: ALStaffName | None = None
    image: ALStaffImage | None = None
    description: str | None = None
    gender: str | None = None
    dateOfBirth: ALStaffDate | None = None
    dateOfDeath: ALStaffDate | None = None
    age: int | None = None

    @override
    def to_edgedb(self):
        data = super().to_edgedb()
        data |= dict(
            description=(self.description if self.description else None),
            gender=self.gender,
            age=self.age,
        )
        if self.name:
            data |= dict(
                name_user_preferred=self.name.userPreferred,
                name_alternative=self.name.alternative,
                name_native=self.name.native,
            )
        if self.image:
            data |= dict(image_large=self.image.large)
        if self.dateOfBirth:
            data |= dict(
                date_of_birth_year=self.dateOfBirth.year,
                date_of_birth_month=self.dateOfBirth.month,
                date_of_birth_day=self.dateOfBirth.day,
            )
        if self.dateOfDeath:
            data |= dict(
                date_of_death_year=self.dateOfDeath.year,
                date_of_death_month=self.dateOfDeath.month,
                date_of_death_day=self.dateOfDeath.day,
            )
        return data


class ALStaffID(BaseModel):
    id: int
    favourites: int


class ALMediaID(BaseModel):
    id: int


CharacterRole = Literal['MAIN', 'SUPPORTING', 'BACKGROUND']


class ALMediaEdge(BaseModel):
    node: ALMediaID
    characterRole: CharacterRole
    voiceActors: list[ALStaffID]


class ALMediaConnection(BaseModel):
    pageInfo: ALPageInfo
    edges: list[ALMediaEdge]


class ALCharaConnection(BaseModel):
    pageInfo: ALPageInfo
    nodes: list[ALCharacterID]


class ALCharacterName(BaseModel):
    userPreferred: str
    alternative: list[str]
    alternativeSpoiler: list[str]
    native: str | None = None


class ALCharacterImage(BaseModel):
    large: str


class ALCharacterDate(BaseModel):
    year: int | None = None
    month: int | None = None
    day: int | None = None


female_prog = re.compile(r'\b(she|her)\b', re.IGNORECASE)
male_prog = re.compile(r'\b(he|his)\b', re.IGNORECASE)


class ALMedia(ALBaseModel):
    characters: ALCharaConnection | None = None
    type: MEDIA_TYPES | None = None
    idMal: int | None = None
    title: ALMediaTitle | None = None
    synonyms: list[str] | None = None
    description: str | None = None
    status: Literal['FINISHED', 'RELEASING', 'NOT_YET_RELEASED', 'CANCELLED', 'HIATUS'] | None = (
        None
    )
    season: Literal['WINTER', 'SPRING', 'SUMMER', 'FALL'] | None = None
    seasonYear: int | None = None
    episodes: int | None = None
    duration: int | None = None
    chapters: int | None = None
    coverImage: ALMediaCoverImage | None = None
    popularity: int | None = None
    isAdult: bool | None = None
    genres: list[str] | None = None
    tags: list[MediaTag] | None = None

    @override
    def to_edgedb(self):
        data = super().to_edgedb()
        data |= dict(
            type=self.type,
            id_mal=self.idMal,
            synonyms=self.synonyms,
            description=(self.description if self.description else None),
            status=self.status,
            season=self.season,
            season_year=self.seasonYear,
            episodes=self.episodes,
            duration=self.duration,
            chapters=self.chapters,
            popularity=self.popularity,
            is_adult=self.isAdult,
            genres=self.genres,
        )
        if self.title is not None:
            data |= dict(
                title_user_preferred=self.title.userPreferred,
                title_english=self.title.english,
                title_native=self.title.native,
            )
        assert self.coverImage is not None
        data |= dict(
            cover_image_extra_large=self.coverImage.extraLarge,
            cover_image_color=self.coverImage.color,
        )
        if self.tags is not None:
            data |= dict(tags=[tag.to_edgedb() for tag in self.tags])
        return data


class ALCharacter(ALBaseModel):
    name: ALCharacterName | None = None
    image: ALCharacterImage | None = None
    description: str | None = None
    gender: str | None = None
    dateOfBirth: ALCharacterDate | None = None
    age: str | None = None
    media: ALMediaConnection | None = None

    @property
    def rank(self):
        assert self.favourites is not None
        if self.favourites >= RANKS[WaicolleRank.S].min_favourites:
            return WaicolleRank.S
        elif self.favourites >= RANKS[WaicolleRank.A].min_favourites:
            return WaicolleRank.A
        elif self.favourites >= RANKS[WaicolleRank.B].min_favourites:
            return WaicolleRank.B
        elif self.favourites >= RANKS[WaicolleRank.C].min_favourites:
            return WaicolleRank.C
        elif self.favourites >= RANKS[WaicolleRank.D].min_favourites:
            return WaicolleRank.D
        else:
            return WaicolleRank.E

    @property
    def fuzzy_gender(self) -> str | None:
        if self.gender is not None:
            return self.gender

        if self.description is not None:
            female = female_prog.findall(self.description)
            male = male_prog.findall(self.description)

            if len(female) != len(male) and max(len(female), len(male)) >= 3 * min(
                len(female), len(male)
            ):
                return 'Female' if len(female) > len(male) else 'Male'

        return None

    @override
    def to_edgedb(self, include_computed: bool = False):
        data = super().to_edgedb()
        assert self.media is not None
        data |= dict(
            description=(self.description if self.description else None),
            gender=self.gender,
            age=self.age,
        )
        if self.name is not None:
            data |= dict(
                name_user_preferred=self.name.userPreferred,
                name_alternative=self.name.alternative,
                name_alternative_spoiler=self.name.alternativeSpoiler,
                name_native=self.name.native,
            )
        if self.image is not None:
            data |= dict(image_large=self.image.large)
        if self.dateOfBirth is not None:
            data |= dict(
                date_of_birth_year=self.dateOfBirth.year,
                date_of_birth_month=self.dateOfBirth.month,
                date_of_birth_day=self.dateOfBirth.day,
            )
        if include_computed:
            data |= dict(rank=self.rank, fuzzy_gender=self.fuzzy_gender)
        return data


class ALStaffCharacterEdge(BaseModel):
    node: ALCharacter
    media: list[ALMedia]


class ALListEntry(BaseModel):
    score: float
    status: str  # don’t know if we need to use a literal here
    progress: int
    media: ALMediaID


##############
# MAL models #
##############
class MALListRespDataEntryListStatus(BaseModel):
    is_rewatching: bool | None = None
    is_rereading: bool | None = None
    num_episodes_watched: int | None = None
    num_chapters_read: int | None = None
    score: int
    status: str


class MALListRespDataEntryNode(BaseModel):
    id: int


class MALListRespDataEntry(BaseModel):
    list_status: MALListRespDataEntryListStatus
    node: MALListRespDataEntryNode


class MALListRespPaging(BaseModel):
    previous: str | None = None
    next: str | None = None


class MALListResp(BaseModel):
    data: list[MALListRespDataEntry]
    paging: MALListRespPaging


##################
# FastAPI models #
##################
class UpsertAnilistAccountBody(BaseModel):
    discord_username: str
    service: ACCOUNT_MERGE_SERVICE
    username: str


class MediaTitleAutocompleteResult(BaseModel):
    id_al: int
    title_user_preferred: str
    type: MediaType


class CharaNameAutocompleteResult(BaseModel):
    id_al: int
    name_user_preferred: str
    name_native: str | None = None


class StaffNameAutocompleteResult(BaseModel):
    id_al: int
    name_user_preferred: str
    name_native: str | None = None
