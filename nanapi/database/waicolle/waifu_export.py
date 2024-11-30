from datetime import datetime
from uuid import UUID

from edgedb import AsyncIOExecutor
from pydantic import BaseModel, TypeAdapter

EDGEQL_QUERY = r"""
with
  players := (select waicolle::Player filter .client = global client),
  waifus := (select waicolle::Waifu filter .client = global client and not .disabled),
  charas := (select anilist::Character filter .id_al in waifus.character.id_al),
select {
  players := players {
    discord_id := .user.discord_id_str,
    discord_username := .user.discord_username,
    tracked := .tracked_characters.id_al
  },
  waifus := waifus {
    id,
    character_id := .character.id_al,
    owner_discord_id := .owner.user.discord_id_str,
    original_owner_discord_id := .original_owner.user.discord_id_str,
    timestamp,
    level,
    locked,
    nanaed,
    blooded,
    trade_locked,
  },
  charas := charas {
    id_al,
    image := str_split(.image_large, '/')[-1],
    favourites,
  },
}
"""


class WaifuExportResultCharas(BaseModel):
    id_al: int
    image: str
    favourites: int


class WaifuExportResultWaifus(BaseModel):
    id: UUID
    character_id: int
    owner_discord_id: str
    original_owner_discord_id: str | None
    timestamp: datetime
    level: int
    locked: bool
    nanaed: bool
    blooded: bool
    trade_locked: bool


class WaifuExportResultPlayers(BaseModel):
    discord_id: str
    discord_username: str
    tracked: list[int]


class WaifuExportResult(BaseModel):
    players: list[WaifuExportResultPlayers]
    waifus: list[WaifuExportResultWaifus]
    charas: list[WaifuExportResultCharas]


adapter = TypeAdapter(WaifuExportResult)


async def waifu_export(
    executor: AsyncIOExecutor,
) -> WaifuExportResult:
    resp = await executor.query_single_json(
        EDGEQL_QUERY,
    )
    return adapter.validate_json(resp, strict=False)
