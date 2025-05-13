from typing import Any, cast

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from gel.errors import ConstraintViolationError
from meilisearch_python_sdk.models.search import SearchResults

from nanapi.database.anilist.account_merge import AccountMergeResult, account_merge
from nanapi.database.anilist.account_select_all import AccountSelectAllResult, account_select_all
from nanapi.database.anilist.c_edge_select_filter_chara import (
    CEdgeSelectFilterCharaResult,
    c_edge_select_filter_chara,
)
from nanapi.database.anilist.c_edge_select_filter_media import (
    CEdgeSelectFilterMediaResult,
    c_edge_select_filter_media,
)
from nanapi.database.anilist.c_edge_select_filter_staff import (
    CEdgeSelectFilterStaffResult,
    c_edge_select_filter_staff,
)
from nanapi.database.anilist.chara_select import CharaSelectResult, chara_select
from nanapi.database.anilist.entry_select_all import (
    ENTRY_SELECT_ALL_MEDIA_TYPE,
    EntrySelectAllResult,
    entry_select_all,
)
from nanapi.database.anilist.entry_select_filter_media import (
    EntrySelectFilterMediaResult,
    entry_select_filter_media,
)
from nanapi.database.anilist.media_select import MediaSelectResult, media_select
from nanapi.database.anilist.staff_select import StaffSelectResult, staff_select
from nanapi.models.anilist import (
    MEDIA_TYPES,
    CharaNameAutocompleteResult,
    MediaTitleAutocompleteResult,
    StaffNameAutocompleteResult,
    UpsertAnilistAccountBody,
)
from nanapi.settings import INSTANCE_NAME
from nanapi.utils.clients import get_edgedb, get_meilisearch
from nanapi.utils.collages import chara_collage, media_collage
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter

router = NanAPIRouter(prefix='/anilist', tags=['anilist'])


############
# Accounts #
############
@router.oauth2.get('/accounts', response_model=list[AccountSelectAllResult])
async def get_accounts():
    """Get all AniList accounts."""
    return await account_select_all(get_edgedb())


@router.oauth2.patch(
    '/accounts/{discord_id}',
    response_model=AccountMergeResult,
    responses={status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel)},
)
async def upsert_account(discord_id: str, body: UpsertAnilistAccountBody):
    """Upsert AniList account for a Discord user."""
    try:
        return await account_merge(get_edgedb(), discord_id=discord_id, **body.model_dump())
    except ConstraintViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.oauth2.get('/accounts/all/entries', response_model=list[EntrySelectAllResult])
async def get_all_entries(type: ENTRY_SELECT_ALL_MEDIA_TYPE | None = None):
    """Get all AniList entries for all accounts."""
    return await entry_select_all(get_edgedb(), media_type=type)


@router.oauth2.get('/accounts/{discord_id}/entries', response_model=list[EntrySelectAllResult])
async def get_account_entries(discord_id: str, type: ENTRY_SELECT_ALL_MEDIA_TYPE | None = None):
    """Get AniList entries for a specific Discord user."""
    return await entry_select_all(get_edgedb(), media_type=type, discord_id=discord_id)


##########
# Medias #
##########
@router.oauth2.get('/medias', response_model=list[MediaSelectResult])
async def get_medias(ids_al: str):
    """Get AniList media objects by IDs."""
    try:
        ids_al_parsed = [int(id_al) for id_al in ids_al.split(',')] if len(ids_al) > 0 else []
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    db_resp = await media_select(get_edgedb(), ids_al=ids_al_parsed)
    return db_resp


@router.oauth2.get('/medias/search', response_model=list[MediaSelectResult])
async def media_search(search: str, type: MEDIA_TYPES | None = None):
    """Search for AniList media by title."""
    async with get_meilisearch() as client:
        index = client.index(f'{INSTANCE_NAME}_medias')
        resp = cast(
            SearchResults[dict[str, Any]],
            await index.search(  # pyright: ignore[reportUnknownMemberType]
                search, limit=25, filter=f'type={type}' if type is not None else None
            ),
        )
    ids = [int(hit['id_al']) for hit in resp.hits]
    data = await media_select(get_edgedb(), ids_al=ids)
    data.sort(key=lambda m: ids.index(m.id_al))
    return data


@router.oauth2.get('/medias/autocomplete', response_model=list[MediaTitleAutocompleteResult])
async def media_title_autocomplete(search: str, type: MEDIA_TYPES | None = None):
    """Autocomplete AniList media titles."""
    async with get_meilisearch() as client:
        index = client.index(f'{INSTANCE_NAME}_medias')
        resp = cast(
            SearchResults[dict[str, Any]],
            await index.search(  # pyright: ignore[reportUnknownMemberType]
                search, limit=25, filter=f'type={type}' if type is not None else None
            ),
        )
        return resp.hits


@router.public.get(
    '/medias/collages',
    response_class=StreamingResponse,
    responses={status.HTTP_400_BAD_REQUEST: dict(model=HTTPExceptionModel)},
)
async def get_medias_collage(ids_al: str):
    """Get a collage image of AniList media covers."""
    try:
        ids_al_parsed = [int(id_al) for id_al in ids_al.split(',')] if len(ids_al) > 0 else []
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    if len(ids_al_parsed) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return StreamingResponse(media_collage(ids_al_parsed), media_type='image/webp')


@router.oauth2.get('/medias/{id_al}/entries', response_model=list[EntrySelectFilterMediaResult])
async def get_media_list_entries(id_al: int):
    """Get AniList entries for a specific media."""
    return await entry_select_filter_media(get_edgedb(), id_al=id_al)


@router.oauth2.get(
    '/medias/{id_al}/edges/charas', response_model=list[CEdgeSelectFilterMediaResult]
)
async def get_media_chara_edges(id_al: int):
    """Get character edges for a specific media."""
    return await c_edge_select_filter_media(get_edgedb(), id_al=id_al)


##########
# Charas #
##########
@router.oauth2.get('/charas', response_model=list[CharaSelectResult])
async def get_charas(ids_al: str):
    """Get AniList characters by IDs."""
    try:
        ids_al_parsed = [int(id_al) for id_al in ids_al.split(',')] if len(ids_al) > 0 else []
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    db_resp = await chara_select(get_edgedb(), ids_al=ids_al_parsed)
    return db_resp


@router.oauth2.get('/charas/search', response_model=list[CharaSelectResult])
async def chara_search(search: str):
    """Search for AniList characters by name."""
    async with get_meilisearch() as client:
        index = client.index(f'{INSTANCE_NAME}_charas')
        resp = cast(SearchResults[dict[str, Any]], await index.search(search, limit=25))  # pyright: ignore[reportUnknownMemberType]
    ids = [int(hit['id_al']) for hit in resp.hits]
    data = await chara_select(get_edgedb(), ids_al=[int(hit['id_al']) for hit in resp.hits])
    data.sort(key=lambda c: ids.index(c.id_al))
    return data


@router.oauth2.get('/charas/autocomplete', response_model=list[CharaNameAutocompleteResult])
async def chara_name_autocomplete(search: str):
    """Autocomplete AniList character names."""
    async with get_meilisearch() as client:
        index = client.index(f'{INSTANCE_NAME}_charas')
        resp = cast(SearchResults[dict[str, Any]], await index.search(search, limit=25))  # pyright: ignore[reportUnknownMemberType]
        return resp.hits


@router.public.get(
    '/charas/collages',
    response_class=StreamingResponse,
    responses={status.HTTP_400_BAD_REQUEST: dict(model=HTTPExceptionModel)},
)
async def get_chara_collage(ids_al: str, hide_no_images: int = 0, blooded: int = 0):
    """Get a collage image of AniList character images."""
    try:
        ids_al_parsed = [int(id_al) for id_al in ids_al.split(',')] if len(ids_al) > 0 else []
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    if len(ids_al_parsed) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    return StreamingResponse(
        chara_collage(ids_al_parsed, hide_no_images=bool(hide_no_images), blooded=bool(blooded)),
        media_type='image/webp',
    )


@router.oauth2.get(
    '/charas/{id_al}/edges/charas',
    response_model=list[CEdgeSelectFilterCharaResult],
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_chara_chara_edges(id_al: int):
    """Get character edges for a specific character."""
    resp = await c_edge_select_filter_chara(get_edgedb(), id_al=id_al)
    return resp


##########
# Staffs #
##########
@router.oauth2.get('/staffs', response_model=list[StaffSelectResult])
async def get_staffs(ids_al: str):
    """Get AniList staff by IDs."""
    try:
        ids_al_parsed = [int(id_al) for id_al in ids_al.split(',')] if len(ids_al) > 0 else []
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

    db_resp = await staff_select(get_edgedb(), ids_al=ids_al_parsed)
    return db_resp


@router.oauth2.get('/staffs/search', response_model=list[StaffSelectResult])
async def staff_search(search: str):
    """Search for AniList staff by name."""
    async with get_meilisearch() as client:
        index = client.index(f'{INSTANCE_NAME}_staffs')
        resp = cast(SearchResults[dict[str, Any]], await index.search(search, limit=25))  # pyright: ignore[reportUnknownMemberType]
    ids = [int(hit['id_al']) for hit in resp.hits]
    data = await staff_select(get_edgedb(), ids_al=[int(hit['id_al']) for hit in resp.hits])
    data.sort(key=lambda s: ids.index(s.id_al))
    return data


@router.oauth2.get('/staffs/autocomplete', response_model=list[StaffNameAutocompleteResult])
async def staff_name_autocomplete(search: str):
    """Autocomplete AniList staff names."""
    async with get_meilisearch() as client:
        index = client.index(f'{INSTANCE_NAME}_staffs')
        resp = cast(SearchResults[dict[str, Any]], await index.search(search, limit=25))  # pyright: ignore[reportUnknownMemberType]
        return resp.hits


@router.oauth2.get(
    '/staffs/{id_al}/edges/charas',
    response_model=list[CEdgeSelectFilterStaffResult],
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_staff_chara_edges(id_al: int):
    """Get character edges for a specific staff."""
    return await c_edge_select_filter_staff(get_edgedb(), id_al=id_al)
