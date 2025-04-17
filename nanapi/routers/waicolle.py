import asyncio
import re
from collections import defaultdict
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, HTTPException, Response, status
from gel import AsyncIOClient, AsyncIOExecutor
from gel.errors import CardinalityViolationError, ConstraintViolationError

from nanapi.database.anilist.c_edge_select_filter_media import (
    c_edge_select_filter_media,
)
from nanapi.database.anilist.c_edge_select_filter_staff import c_edge_select_filter_staff
from nanapi.database.anilist.chara_get_random import chara_get_random
from nanapi.database.anilist.chara_select import CharaSelectResult, chara_select
from nanapi.database.anilist.media_select import media_select
from nanapi.database.anilist.staff_select import staff_select
from nanapi.database.waicolle.collection_add_media import (
    CollectionAddMediaResult,
    collection_add_media,
)
from nanapi.database.waicolle.collection_add_staff import (
    CollectionAddStaffResult,
    collection_add_staff,
)
from nanapi.database.waicolle.collection_delete import CollectionDeleteResult, collection_delete
from nanapi.database.waicolle.collection_get_by_id import (
    CollectionGetByIdResult,
    collection_get_by_id,
)
from nanapi.database.waicolle.collection_insert import CollectionInsertResult, collection_insert
from nanapi.database.waicolle.collection_remove_media import (
    CollectionRemoveMediaResult,
    collection_remove_media,
)
from nanapi.database.waicolle.collection_remove_staff import (
    CollectionRemoveStaffResult,
    collection_remove_staff,
)
from nanapi.database.waicolle.coupon_add_player import coupon_add_player
from nanapi.database.waicolle.coupon_delete import CouponDeleteResult, coupon_delete
from nanapi.database.waicolle.coupon_get_by_code import coupon_get_by_code
from nanapi.database.waicolle.coupon_insert import CouponInsertResult, coupon_insert
from nanapi.database.waicolle.coupon_select_all import CouponSelectAllResult, coupon_select_all
from nanapi.database.waicolle.medias_pool_export import MediasPoolExportResult, medias_pool_export
from nanapi.database.waicolle.player_add_coins import PlayerAddCoinsResult, player_add_coins
from nanapi.database.waicolle.player_add_collection import (
    PlayerAddCollectionResult,
    player_add_collection,
)
from nanapi.database.waicolle.player_add_media import PlayerAddMediaResult, player_add_media
from nanapi.database.waicolle.player_add_staff import PlayerAddStaffResult, player_add_staff
from nanapi.database.waicolle.player_collection_stats import (
    PlayerCollectionStatsResult,
    player_collection_stats,
)
from nanapi.database.waicolle.player_freeze import PlayerFreezeResult, player_freeze
from nanapi.database.waicolle.player_get_by_user import PlayerGetByUserResult, player_get_by_user
from nanapi.database.waicolle.player_media_stats import PlayerMediaStatsResult, player_media_stats
from nanapi.database.waicolle.player_merge import PlayerMergeResult, player_merge
from nanapi.database.waicolle.player_remove_collection import (
    PlayerRemoveCollectionResult,
    player_remove_collection,
)
from nanapi.database.waicolle.player_remove_media import (
    PlayerRemoveMediaResult,
    player_remove_media,
)
from nanapi.database.waicolle.player_remove_staff import (
    PlayerRemoveStaffResult,
    player_remove_staff,
)
from nanapi.database.waicolle.player_select_all import player_select_all
from nanapi.database.waicolle.player_select_by_chara import (
    PlayerSelectByCharaResult,
    player_select_by_chara,
)
from nanapi.database.waicolle.player_staff_stats import PlayerStaffStatsResult, player_staff_stats
from nanapi.database.waicolle.player_tracked_items import (
    PlayerTrackedItemsResult,
    player_tracked_items,
)
from nanapi.database.waicolle.rerollop_insert import rerollop_insert
from nanapi.database.waicolle.rollop_insert import rollop_insert
from nanapi.database.waicolle.trade_commit import trade_commit
from nanapi.database.waicolle.trade_delete import TradeDeleteResult, trade_delete
from nanapi.database.waicolle.trade_get_by_id import trade_get_by_id
from nanapi.database.waicolle.trade_insert import trade_insert
from nanapi.database.waicolle.trade_select import TradeSelectResult, trade_select
from nanapi.database.waicolle.waifu_ascendable import waifu_ascendable
from nanapi.database.waicolle.waifu_bulk_update import WaifuBulkUpdateResult, waifu_bulk_update
from nanapi.database.waicolle.waifu_change_owner import waifu_change_owner
from nanapi.database.waicolle.waifu_edged import waifu_edged
from nanapi.database.waicolle.waifu_export import WaifuExportResult, waifu_export
from nanapi.database.waicolle.waifu_insert import waifu_insert
from nanapi.database.waicolle.waifu_replace_custom_position import (
    WaifuReplaceCustomPositionResult,
    waifu_replace_custom_position,
)
from nanapi.database.waicolle.waifu_select import WaifuSelectResult, waifu_select
from nanapi.database.waicolle.waifu_select_by_chara import (
    WaifuSelectByCharaResult,
    waifu_select_by_chara,
)
from nanapi.database.waicolle.waifu_select_by_user import waifu_select_by_user
from nanapi.database.waicolle.waifu_track_unlocked import waifu_track_unlocked
from nanapi.database.waicolle.waifu_update_ascended_from import waifu_update_ascended_from
from nanapi.database.waicolle.waifu_update_custom_image_name import (
    WaifuUpdateCustomImageNameResult,
    waifu_update_custom_image_name,
)
from nanapi.models.waicolle import (
    COLLAGE_CHOICE,
    RANKS,
    AddPlayerCoinsBody,
    BulkUpdateWaifusBody,
    CollageChoice,
    CollageResult,
    CollectionAlbumResult,
    CollectionNameAutocompleteResult,
    CommitTradeResponse,
    CustomizeWaifuBody,
    DonatePlayerCoinsBody,
    MediaAlbumResult,
    NewCollectionBody,
    NewCouponBody,
    NewLootBody,
    NewOfferingBody,
    NewTradeBody,
    PlayerSelectResult,
    PlayerTrackReversedResult,
    Rank,
    ReorderWaifuBody,
    RerollBody,
    RerollResponse,
    RollData,
    S,
    StaffAlbumResult,
    UpsertPlayerBody,
)
from nanapi.settings import INSTANCE_NAME, TZ
from nanapi.utils.clients import get_edgedb, get_meilisearch
from nanapi.utils.collages import chara_album, waifu_collage
from nanapi.utils.fastapi import (
    HTTPExceptionModel,
    NanAPIRouter,
    client_id_param,
    get_client_edgedb,
)
from nanapi.utils.waicolle import (
    RE_SYMBOLES,
    REROLLS_MAX_RANKS,
    RNG,
    ROLLS,
    TagRoll,
    UserRoll,
)

router = NanAPIRouter(prefix='/waicolle', tags=['waicolle'])


###########
# Players #
###########
@router.oauth2_client.get('/players', response_model=list[PlayerSelectResult])
async def get_players(
    chara_id_al: int | None = None, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get all players or filter by character ID."""
    if chara_id_al is not None:
        return await player_select_by_chara(edgedb, id_al=chara_id_al)
    else:
        return await player_select_all(edgedb)


@router.oauth2_client_restricted.patch('/players/{discord_id}', response_model=PlayerMergeResult)
async def upsert_player(
    discord_id: int, body: UpsertPlayerBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Upsert (merge) a player by Discord ID."""
    return await player_merge(edgedb, discord_id=discord_id, **body.model_dump())


@router.oauth2_client.get(
    '/players/{discord_id}',
    response_model=PlayerGetByUserResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player(discord_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get a player by Discord ID."""
    resp = await player_get_by_user(edgedb, discord_id=discord_id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.put(
    '/players/{discord_id}/freeze',
    response_model=PlayerFreezeResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def freeze_player(discord_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Freeze a player by Discord ID."""
    resp = await player_freeze(edgedb, discord_id=discord_id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.post(
    '/players/{discord_id}/coins/add',
    response_model=PlayerAddCoinsResult,
    responses={
        status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel),
        status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel),
    },
)
async def add_player_coins(
    discord_id: int, body: AddPlayerCoinsBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Add coins to a player."""
    try:
        resp = await player_add_coins(edgedb, discord_id=discord_id, **body.model_dump())
    except ConstraintViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.post(
    '/players/{discord_id}/coins/donate',
    response_model=list[PlayerAddCoinsResult],
    responses={
        status.HTTP_400_BAD_REQUEST: dict(model=HTTPExceptionModel),
        status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel),
        status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel),
    },
)
async def donate_player_coins(
    discord_id: int,
    to_discord_id: int,
    body: DonatePlayerCoinsBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Donate coins from one player to another."""
    if discord_id == to_discord_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot donate to yourself'
        )
    if body.moecoins < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot donate negative moecoins'
        )

    async for tx in edgedb.transaction():
        async with tx:
            try:
                resp1 = await player_add_coins(tx, discord_id=discord_id, moecoins=-body.moecoins)
            except ConstraintViolationError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
            if resp1 is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=f'Player[{discord_id}] Not Found'
                )

            try:
                resp2 = await player_add_coins(
                    tx, discord_id=to_discord_id, moecoins=body.moecoins
                )
            except ConstraintViolationError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
            if resp2 is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f'Player[{to_discord_id}] Not Found',
                )

            return resp1, resp2


@router.oauth2_client_restricted.post(
    '/players/{discord_id}/roll',
    response_model=list[WaifuSelectResult],
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_204_NO_CONTENT: {},
        status.HTTP_400_BAD_REQUEST: dict(model=HTTPExceptionModel),
        status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel),
        status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel),
    },
)
async def player_roll(
    discord_id: int,
    roll_id: str | None = None,
    coupon_code: str | None = None,
    nb: int | None = None,
    pool_discord_id: int | None = None,
    reason: str | None = None,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Perform a waifu roll for a player."""
    async for tx in edgedb.transaction():
        async with tx:
            # Check if the player exists
            player = await player_get_by_user(tx, discord_id=discord_id)
            if player is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail='Player Not Found'
                )
            if player.frozen_at is not None:
                return Response(status_code=status.HTTP_204_NO_CONTENT)

            # Get Roll
            if roll_id is not None:
                roll_getter = ROLLS.get(roll_id, None)
                if roll_getter is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail='Roll Not Found'
                    )
                roll = roll_getter()
                reason = reason if reason is not None else roll_id
            elif coupon_code is not None:
                # Check eligibility
                coupon = await coupon_get_by_code(tx, code=coupon_code)
                if coupon is None:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail='Coupon Not Found'
                    )
                if discord_id in [p.user.discord_id for p in coupon.claimed_by]:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT, detail='Coupon already claimed'
                    )
                await coupon_add_player(tx, code=coupon_code, discord_id=discord_id)
                roll = UserRoll(3)
                reason = reason if reason is not None else 'coupon'
            elif nb is not None:
                roll = UserRoll(nb)
                reason = reason if reason is not None else 'drop'
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

            await roll.load(tx)

            # Pay price
            price = await roll.get_price(tx, discord_id)
            if price > 0:
                try:
                    await player_add_coins(tx, discord_id=discord_id, moecoins=-price)
                except ConstraintViolationError as e:
                    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

            # Dry roll
            if pool_discord_id is None:
                pool_discord_id = discord_id
            charas_ids = await roll.roll(tx, pool_discord_id)

            # Insert waifus
            new_waifus = await waifu_insert(tx, discord_id=discord_id, charas_ids=charas_ids)

            # Do after task
            await roll.after(tx, discord_id)

            await rollop_insert(
                tx,
                author_discord_id=discord_id,
                received_ids=[w.id for w in new_waifus],
                reason=reason,
                moecoins=price,
            )

            return new_waifus


@router.oauth2_client.get(
    '/players/{discord_id}/tracks',
    response_model=PlayerTrackedItemsResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_tracked_items(
    discord_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get tracked items for a player."""
    try:
        return await player_tracked_items(edgedb, discord_id=discord_id)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client.get(
    '/players/{discord_id}/tracks/unlocked',
    response_model=list[WaifuSelectResult],
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_track_unlocked(
    discord_id: int, hide_singles: int = 0, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get unlocked waifus for a player."""
    try:
        return await waifu_track_unlocked(
            edgedb, discord_id=discord_id, hide_singles=bool(hide_singles)
        )
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client.get(
    '/players/{discord_id}/tracks/reversed',
    response_model=list[PlayerTrackReversedResult],
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_track_reversed(
    discord_id: int, hide_singles: int = 0, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get reversed track information for a player."""
    try:
        unlocked = await waifu_select_by_user(
            edgedb, discord_id=discord_id, locked=False, trade_locked=False, blooded=False
        )
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    id_al_set = {w.character.id_al for w in unlocked}
    async with asyncio.TaskGroup() as tg:
        tasks = [
            (
                id_al,
                tg.create_task(player_select_by_chara(edgedb, id_al=id_al)),
                tg.create_task(waifu_select_by_chara(edgedb, id_al=id_al)),
            )
            for id_al in id_al_set
        ]

    resp_map: dict[
        int,
        tuple[
            dict[int, PlayerSelectByCharaResult],
            dict[int, list[WaifuSelectByCharaResult]],
        ],
    ] = {}
    for id_al, ttask, wtask in tasks:
        trackers_map = {t.user.discord_id: t for t in ttask.result() if t.frozen_at is None}
        locked_map = defaultdict[int, list[WaifuSelectByCharaResult]](list)
        for w in wtask.result():
            if w.locked and not w.frozen:
                locked_map[w.owner.user.discord_id].append(w)
                trackers_map.pop(w.owner.user.discord_id, None)
        if hide_singles:
            locked_map = {k: v for k, v in locked_map.items() if len(v) != 1}
        resp_map[id_al] = (trackers_map, locked_map)

    resp = []
    for uwaifu in unlocked:
        trackers_map, locked_map = resp_map[uwaifu.character.id_al]
        if len(trackers_map) > 0 or len(locked_map) > 0:
            resp.append(
                dict(
                    waifu=uwaifu,
                    trackers_not_owners=trackers_map.values(),
                    locked=sum(locked_map.values(), []),
                )
            )

    return resp


@router.oauth2_client.get(
    '/players/{discord_id}/tracks/medias/{id_al}',
    response_model=PlayerMediaStatsResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_media_stats(
    discord_id: int, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get media stats for a player."""
    try:
        return await player_media_stats(edgedb, discord_id=discord_id, id_al=id_al)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client_restricted.put(
    '/players/{discord_id}/tracks/medias/{id_al}',
    response_model=PlayerAddMediaResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def player_track_media(
    discord_id: int, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Track a media for a player."""
    try:
        return await player_add_media(edgedb, discord_id=discord_id, id_al=id_al)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client_restricted.delete(
    '/players/{discord_id}/tracks/medias/{id_al}',
    response_model=PlayerRemoveMediaResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def player_untrack_media(
    discord_id: int, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Untrack a media for a player."""
    resp = await player_remove_media(edgedb, discord_id=discord_id, id_al=id_al)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client.get(
    '/players/{discord_id}/tracks/staffs/{id_al}',
    response_model=PlayerStaffStatsResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_staff_stats(
    discord_id: int, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get staff stats for a player."""
    try:
        return await player_staff_stats(edgedb, discord_id=discord_id, id_al=id_al)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client_restricted.put(
    '/players/{discord_id}/tracks/staffs/{id_al}',
    response_model=PlayerAddStaffResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def player_track_staff(
    discord_id: int, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Track a staff for a player."""
    try:
        return await player_add_staff(edgedb, discord_id=discord_id, id_al=id_al)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client_restricted.delete(
    '/players/{discord_id}/tracks/staffs/{id_al}',
    response_model=PlayerRemoveStaffResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def player_untrack_staff(
    discord_id: int, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Untrack a staff for a player."""
    resp = await player_remove_staff(edgedb, discord_id=discord_id, id_al=id_al)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client.get(
    '/players/{discord_id}/tracks/collections/{id}',
    response_model=PlayerCollectionStatsResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_collection_stats(
    discord_id: int, id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get collection stats for a player."""
    try:
        return await player_collection_stats(edgedb, discord_id=discord_id, id=id)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client_restricted.put(
    '/players/{discord_id}/tracks/collections/{id}',
    response_model=PlayerAddCollectionResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def player_track_collection(
    discord_id: int, id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Track a collection for a player."""
    try:
        return await player_add_collection(edgedb, discord_id=discord_id, id=id)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client_restricted.delete(
    '/players/{discord_id}/tracks/collections/{id}',
    response_model=PlayerRemoveCollectionResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def player_untrack_collection(
    discord_id: int, id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Untrack a collection for a player."""
    resp = await player_remove_collection(edgedb, discord_id=discord_id, id=id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


############
# Collages #
############
@router.oauth2_client.get(
    '/players/{discord_id}/collages/waifus',
    response_model=CollageResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_collage(
    discord_id: int, filter: COLLAGE_CHOICE, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Get waifu collage for a player."""
    _filter = CollageChoice(filter)

    try:
        if _filter is CollageChoice.EDGED:
            resp = await waifu_edged(edgedb, discord_id=discord_id)
            waifus = sorted(
                (group.elements[0] for group in resp), key=lambda w: w.timestamp, reverse=True
            )
        else:
            kwargs = dict(blooded=False)
            if _filter is CollageChoice.FULL:
                pass
            elif _filter is CollageChoice.LOCKED:
                kwargs['locked'] = True
            elif _filter is CollageChoice.UNLOCKED:
                kwargs['locked'] = False
            elif _filter is CollageChoice.ASCENDED:
                kwargs['ascended'] = True
            elif _filter is CollageChoice.CUSTOM:
                kwargs['custom_collage'] = True
            else:
                raise RuntimeError('How did you get there?')

            waifus = await waifu_select_by_user(
                edgedb, discord_id=discord_id, characters_ids_al=None, **kwargs
            )
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    url = None

    if waifus:
        url = await waifu_collage(list(waifus))

    chara_ids_set = {w.character.id_al for w in waifus}

    return CollageResult(url=url, total=len(chara_ids_set))


@router.oauth2_client.get(
    '/players/{discord_id}/collages/medias/{id_al}',
    response_model=MediaAlbumResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_media_album(
    discord_id: int,
    id_al: int,
    owned_only: int = 0,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Get media album collage for a player."""
    medias = await media_select(edgedb, ids_al=[id_al])
    if not medias:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    media = medias[0]

    edges = await c_edge_select_filter_media(edgedb, id_al=media.id_al)

    chara_map = {
        e.character.id_al: e.character
        for e in edges
        if not e.character.image_large.endswith('/default.jpg')
    }
    sorted_charas = sorted(chara_map.values(), key=lambda c: c.favourites, reverse=True)

    url = None
    owned = 0
    if sorted_charas:
        waifus = await waifu_select_by_user(
            edgedb,
            discord_id=discord_id,
            characters_ids_al=[c.id_al for c in sorted_charas],
            blooded=False,
        )

        url = await chara_album(list(sorted_charas), list(waifus), owned_only=bool(owned_only))

        chara_ids_set = {w.character.id_al for w in waifus}
        owned = len(chara_ids_set)

    return MediaAlbumResult(url=url, total=len(sorted_charas), owned=owned, media=media)


@router.oauth2_client.get(
    '/players/{discord_id}/collages/staffs/{id_al}',
    response_model=StaffAlbumResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_staff_album(
    discord_id: int,
    id_al: int,
    owned_only: int = 0,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Get staff album collage for a player."""
    staffs = await staff_select(edgedb, ids_al=[id_al])
    if not staffs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    staff = staffs[0]

    edges = await c_edge_select_filter_staff(edgedb, id_al=staff.id_al)

    chara_map = {
        e.character.id_al: e.character
        for e in edges
        if not e.character.image_large.endswith('/default.jpg')
    }
    sorted_charas = sorted(chara_map.values(), key=lambda c: c.favourites, reverse=True)

    url = None
    owned = 0
    if sorted_charas:
        waifus = await waifu_select_by_user(
            edgedb,
            discord_id=discord_id,
            characters_ids_al=[c.id_al for c in sorted_charas],
            blooded=False,
        )

        url = await chara_album(list(sorted_charas), list(waifus), owned_only=bool(owned_only))

        chara_ids_set = {w.character.id_al for w in waifus}
        owned = len(chara_ids_set)

    return StaffAlbumResult(url=url, total=len(sorted_charas), owned=owned, staff=staff)


@router.oauth2_client.get(
    '/players/{discord_id}/collages/collections/{id}',
    response_model=CollectionAlbumResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_player_collection_album(
    discord_id: int,
    id: UUID,
    owned_only: int = 0,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Get collection album collage for a player."""
    collec = await collection_get_by_id(edgedb, id=id)
    if not collec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    resp = await chara_select(edgedb, ids_al=collec.characters_ids_al)

    chara_map = {c.id_al: c for c in resp if not c.image_large.endswith('/default.jpg')}

    sorted_charas = sorted(chara_map.values(), key=lambda c: c.favourites, reverse=True)

    url = None
    owned = 0
    if sorted_charas:
        waifus = await waifu_select_by_user(
            edgedb,
            discord_id=discord_id,
            characters_ids_al=[c.id_al for c in sorted_charas],
            blooded=False,
        )

        url = await chara_album(list(sorted_charas), list(waifus), owned_only=bool(owned_only))

        chara_ids_set = {w.character.id_al for w in waifus}
        owned = len(chara_ids_set)

    return CollectionAlbumResult(url=url, total=len(sorted_charas), owned=owned, collection=collec)


##########
# Waifus #
##########
@router.oauth2_client.get(
    '/waifus',
    response_model=list[WaifuSelectResult],
    responses={
        status.HTTP_400_BAD_REQUEST: dict(model=HTTPExceptionModel),
        status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel),
    },
)
async def get_waifus(
    ids: str | None = None,
    discord_id: int | None = None,
    level: int | None = None,
    locked: int | None = None,
    trade_locked: int | None = None,
    blooded: int | None = None,
    nanaed: int | None = None,
    custom_collage: int | None = None,
    as_og: int | None = None,
    ascended: int | None = None,
    edged: int = 0,
    ascendable: int = 0,
    chara_id_al: int | None = None,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Get waifus with various filters."""
    if ids is not None:
        try:
            parsed_ids = [UUID(id) for id in ids.split(',')] if len(ids) > 0 else []
        except ValueError:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
        return await waifu_select(edgedb, ids=parsed_ids)

    if chara_id_al is not None:
        return await waifu_select_by_chara(edgedb, id_al=chara_id_al)
    elif discord_id is not None:
        try:
            if bool(edged):
                resp = await waifu_edged(edgedb, discord_id=discord_id)
                return sorted(
                    (group.elements[0] for group in resp), key=lambda w: w.timestamp, reverse=True
                )
            elif bool(ascendable):
                resp = await waifu_ascendable(edgedb, discord_id=discord_id)
                return sorted(
                    (group.elements[0] for group in resp), key=lambda w: w.timestamp, reverse=True
                )
            else:
                return await waifu_select_by_user(
                    edgedb,
                    discord_id=discord_id,
                    level=level,
                    locked=bool(locked) if locked is not None else None,
                    trade_locked=(bool(trade_locked) if trade_locked is not None else None),
                    blooded=bool(blooded) if blooded is not None else None,
                    nanaed=bool(nanaed) if nanaed is not None else None,
                    custom_collage=(bool(custom_collage) if custom_collage is not None else None),
                    as_og=bool(as_og) if as_og is not None else None,
                    ascended=bool(ascended) if ascended is not None else None,
                )
        except CardinalityViolationError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@router.oauth2_client_restricted.patch('/waifus', response_model=list[WaifuBulkUpdateResult])
async def bulk_update_waifus(
    body: BulkUpdateWaifusBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Bulk update waifus."""
    return await waifu_bulk_update(edgedb, **body.model_dump())


@router.oauth2_client_restricted.post(
    '/waifus/reroll', response_model=RerollResponse, status_code=status.HTTP_201_CREATED
)
async def reroll(body: RerollBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Reroll waifus for a player."""
    async for tx in edgedb.transaction():
        async with tx:
            rerolled = await waifu_select(tx, ids=body.waifus_ids)

            nanaed = [w.id for w in rerolled if w.nanaed]
            await waifu_bulk_update(tx, ids=nanaed, blooded=True)

            not_nanaed = [w.id for w in rerolled if not w.nanaed]
            await waifu_bulk_update(tx, ids=not_nanaed, nanaed=True)
            await waifu_change_owner(tx, ids=not_nanaed, discord_id=body.bot_discord_id)

            nanascends = await ascend_all(tx, body.bot_discord_id)

            charas = await chara_select(tx, ids_al=[w.character.id_al for w in rerolled])
            chara_map = {c.id_al: c for c in charas}

            min_rank = S
            for waifu in rerolled:
                chara = chara_map[waifu.character.id_al]
                rank = RANKS[chara.rank]
                if rank < min_rank:
                    min_rank = rank

            REROLL_PRICE = 3
            nb_indices = len(rerolled)
            if nb_indices % REROLL_PRICE:
                nb_indices += RNG.integers(0, REROLL_PRICE)
            nb_to_roll = nb_indices // REROLL_PRICE

            roll = UserRoll(nb_to_roll, min_rank=min_rank, max_rank=REROLLS_MAX_RANKS[min_rank])
            await roll.load(tx)
            charas_ids = await roll.roll(tx, body.player_discord_id)
            resp = await waifu_insert(tx, discord_id=body.player_discord_id, charas_ids=charas_ids)
            await roll.after(tx, body.player_discord_id)

            await rerollop_insert(
                tx,
                author_discord_id=body.player_discord_id,
                received_ids=[w.id for w in resp],
                rerolled_ids=[w.id for w in rerolled],
            )

            return dict(obtained=resp, nanascends=nanascends)


async def ascend_all(tx: AsyncIOExecutor, discord_id: int) -> list[WaifuSelectResult]:
    """Ascend all eligible waifus for a player."""
    ascended = []
    while True:
        ascendables = await waifu_ascendable(tx, discord_id=discord_id)
        _ascended = []
        for ascendable in ascendables:
            elements = sorted(ascendable.elements, key=lambda e: e.timestamp)
            while len(elements) >= 4:
                to_ascend = elements[0]
                to_delete = elements[1:4]
                resp = await waifu_bulk_update(
                    tx,
                    ids=[to_ascend.id],
                    level=to_ascend.level + 1,
                    timestamp=datetime.now(tz=TZ),
                )
                await waifu_update_ascended_from(
                    tx,
                    ascended_id=to_ascend.id,
                    ascended_from_ids=[e.id for e in to_delete],
                )
                _ascended.append(resp[0])
                elements = elements[4:]
        if _ascended:
            ascended += _ascended
        else:
            break
    return ascended


@router.oauth2_client_restricted.delete('/waifus/expired', response_model=list[WaifuSelectResult])
async def blood_expired_waifus(
    discord_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Blood expired waifus for a player."""
    async for tx in edgedb.transaction():
        async with tx:
            waifus = await waifu_select_by_user(
                tx,
                discord_id=discord_id,
                level=0,
                locked=False,
                trade_locked=False,
                blooded=False,
                nanaed=True,
            )
            expired = [w for w in waifus if w.timestamp < datetime.now(tz=TZ) - timedelta(days=30)]
            return await waifu_bulk_update(tx, ids=[w.id for w in expired], blooded=True)


@router.oauth2_client_restricted.patch(
    '/waifus/{id}/customs',
    response_model=WaifuUpdateCustomImageNameResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def customize_waifu(
    id: UUID, body: CustomizeWaifuBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Customize waifu image name."""
    resp = await waifu_update_custom_image_name(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.patch(
    '/waifus/{id}/reorder',
    response_model=WaifuReplaceCustomPositionResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def reorder_waifu(
    id: UUID, body: ReorderWaifuBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Reorder waifu custom position."""
    resp = await waifu_replace_custom_position(edgedb, id=id, **body.model_dump())
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.post(
    '/waifus/{id}/ascend',
    response_model=WaifuSelectResult,
    responses={
        status.HTTP_400_BAD_REQUEST: dict(model=HTTPExceptionModel),
        status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel),
    },
)
async def ascend_waifu(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Ascend a waifu by ID."""
    async for tx in edgedb.transaction():
        async with tx:
            waifus = await waifu_select(tx, ids=[id])
            if not waifus:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            waifu = waifus[0]

            ascendables = await waifu_ascendable(tx, discord_id=waifu.owner.user.discord_id)

            for ascendable in ascendables:
                key = ascendable.key
                if key.chara_id_al == waifu.character.id_al and key.level == waifu.level:
                    elements = ascendable.elements
                    break
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

            elements = sorted(elements, key=lambda e: e.timestamp)

            to_ascend = elements[0]
            to_delete = elements[1:4]

            ascended = await waifu_bulk_update(
                tx, ids=[to_ascend.id], level=to_ascend.level + 1, timestamp=datetime.now(tz=TZ)
            )
            await waifu_update_ascended_from(
                tx,
                ascended_id=to_ascend.id,
                ascended_from_ids=[e.id for e in to_delete],
            )

            return ascended[0]


@router.oauth2_client_restricted.post(
    '/waifus/{id}/blood',
    response_model=CharaSelectResult,
    responses={
        status.HTTP_400_BAD_REQUEST: dict(model=HTTPExceptionModel),
        status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel),
    },
)
async def blood_waifu(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Blood a waifu by ID."""
    async for tx in edgedb.transaction():
        async with tx:
            waifus = await waifu_select(tx, ids=[id])
            if not waifus:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            waifu = waifus[0]

            if waifu.blooded:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail='Already Blooded'
                )

            await waifu_bulk_update(tx, ids=[id], blooded=True)

            resp = await chara_select(tx, ids_al=[waifu.character.id_al])
            chara = resp[0]

            await player_add_coins(
                tx,
                discord_id=waifu.owner.user.discord_id,
                blood_shards=RANKS[chara.rank].blood_shards * pow(4, waifu.level),
            )

            return chara


##########
# Trades #
##########
@router.oauth2_client.get('/trades', response_model=list[TradeSelectResult])
async def trade_index(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get all trades."""
    return await trade_select(edgedb)


@router.oauth2_client_restricted.post(
    '/trades', response_model=TradeSelectResult, status_code=status.HTTP_201_CREATED
)
async def new_trade(body: NewTradeBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Create a new trade."""
    return await trade_insert(edgedb, **body.model_dump())


@router.oauth2_client_restricted.post(
    '/trades/offerings',
    response_model=TradeSelectResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def new_offering(body: NewOfferingBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Create a new offering trade."""
    waifus = await waifu_select_by_chara(edgedb, id_al=body.chara_id_al)
    waifus = sorted(waifus, key=lambda w: (w.level, w.timestamp))
    for waifu in waifus:
        if (
            waifu.owner.user.discord_id == body.bot_discord_id
            and not waifu.blooded
            and not waifu.trade_locked
        ):
            to_trade = waifu
            break
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    resp = await chara_select(edgedb, ids_al=[to_trade.character.id_al])
    chara = resp[0]
    rank = RANKS[chara.rank]

    return await trade_insert(
        edgedb,
        author_discord_id=body.player_discord_id,
        received_ids=[to_trade.id],
        offeree_discord_id=body.bot_discord_id,
        offered_ids=[],
        blood_shards=rank.blood_price * pow(4, to_trade.level),
    )


@router.oauth2_client_restricted.post(
    '/trades/loots',
    response_model=TradeSelectResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def new_loot(body: NewLootBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Create a new loot trade."""
    waifus = await waifu_select_by_chara(edgedb, id_al=body.chara_id_al)
    waifus = sorted(waifus, key=lambda w: (w.level, w.timestamp))
    for waifu in waifus:
        if all((waifu.frozen, not waifu.blooded, not waifu.locked, not waifu.trade_locked)):
            to_trade = waifu
            break
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return await trade_insert(
        edgedb,
        author_discord_id=body.player_discord_id,
        received_ids=[to_trade.id],
        offeree_discord_id=to_trade.owner.user.discord_id,
        offered_ids=[],
    )


@router.oauth2_client_restricted.delete(
    '/trades/{id}', response_model=TradeDeleteResult, responses={status.HTTP_204_NO_CONTENT: {}}
)
async def cancel_trade(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Cancel a trade by ID."""
    resp = await trade_delete(edgedb, id=id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client_restricted.post(
    '/trades/{id}/commit',
    response_model=CommitTradeResponse,
    responses={
        status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel),
        status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel),
    },
)
async def commit_trade(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Commit a trade by ID."""
    async for tx in edgedb.transaction():
        async with tx:
            trade = await trade_get_by_id(tx, id=id)
            if trade is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            if trade.completed_at is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT)
            commit = await trade_commit(tx, id=id)
            assert commit is not None

            try:
                await player_add_coins(
                    tx,
                    discord_id=trade.author.user.discord_id,
                    blood_shards=-trade.blood_shards or 0,
                )
                await player_add_coins(
                    tx,
                    discord_id=trade.offeree.user.discord_id,
                    blood_shards=trade.blood_shards or 0,
                )
            except ConstraintViolationError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

            resp3 = await waifu_change_owner(
                tx, discord_id=trade.author.user.discord_id, ids=[w.id for w in trade.received]
            )
            resp4 = await waifu_change_owner(
                tx, discord_id=trade.offeree.user.discord_id, ids=[w.id for w in trade.offered]
            )

            return dict(received=resp3, offered=resp4)


###############
# Collections #
###############
@router.oauth2_client_restricted.post(
    '/collections',
    response_model=CollectionInsertResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel)},
)
async def new_collection(
    body: NewCollectionBody,
    client_id: UUID = Depends(client_id_param),
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Create a new collection."""
    async for tx in edgedb.transaction():
        async with tx:
            try:
                resp = await collection_insert(tx, **body.model_dump())
            except ConstraintViolationError as e:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
            async with get_meilisearch() as client:
                index = client.index(f'{INSTANCE_NAME}_collections_{client_id}')
                doc = dict(
                    id=str(resp.id), name=resp.name, author_discord_id=resp.author.user.discord_id
                )
                await index.add_documents([doc], primary_key='id')
            await player_add_collection(tx, discord_id=body.discord_id, id=resp.id)
            return resp


@router.oauth2_client.get(
    '/collections/autocomplete', response_model=list[CollectionNameAutocompleteResult]
)
async def collection_name_autocomplete(search: str, client_id: UUID = Depends(client_id_param)):
    """Autocomplete collection names."""
    async with get_meilisearch() as client:
        index = client.index(f'{INSTANCE_NAME}_collections_{client_id}')
        resp = await index.search(search, limit=25)
        return resp.hits


@router.oauth2_client.get(
    '/collections/{id}',
    response_model=CollectionGetByIdResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_collection(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get a collection by ID."""
    resp = await collection_get_by_id(edgedb, id=id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.delete(
    '/collections/{id}',
    response_model=CollectionDeleteResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def delete_collection(
    id: UUID,
    client_id: UUID = Depends(client_id_param),
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Delete a collection by ID."""
    async for tx in edgedb.transaction():
        async with tx:
            resp = await collection_delete(tx, id=id)
            if resp is None:
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            async with get_meilisearch() as client:
                index = client.index(f'{INSTANCE_NAME}_collections_{client_id}')
                await index.delete_document(str(resp.id))
            return resp


@router.oauth2_client_restricted.put(
    '/collections/{id}/medias/{id_al}',
    response_model=CollectionAddMediaResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def collection_track_media(
    id: UUID, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Track a media for a collection."""
    try:
        return await collection_add_media(edgedb, id=id, id_al=id_al)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client_restricted.put(
    '/collections/{id}/staffs/{id_al}',
    response_model=CollectionAddStaffResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def collection_track_staff(
    id: UUID, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Track a staff for a collection."""
    try:
        return await collection_add_staff(edgedb, id=id, id_al=id_al)
    except CardinalityViolationError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.oauth2_client_restricted.delete(
    '/collections/{id}/medias/{id_al}',
    response_model=CollectionRemoveMediaResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def collection_untrack_media(
    id: UUID, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Untrack a media for a collection."""
    resp = await collection_remove_media(edgedb, id=id, id_al=id_al)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


@router.oauth2_client_restricted.delete(
    '/collections/{id}/staffs/{id_al}',
    response_model=CollectionRemoveStaffResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def collection_untrack_staff(
    id: UUID, id_al: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    """Untrack a staff for a collection."""
    resp = await collection_remove_staff(edgedb, id=id, id_al=id_al)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


###########
# Coupons #
###########
@router.oauth2_client.get('/coupons', response_model=list[CouponSelectAllResult])
async def get_coupons(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get all coupons."""
    return await coupon_select_all(edgedb)


@router.oauth2_client_restricted.post(
    '/coupons',
    response_model=CouponInsertResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel)},
)
async def new_coupon(body: NewCouponBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Create a new coupon."""
    code = body.code
    if code is None:
        chara = await chara_get_random(edgedb)
        if chara is None:
            # should not happen if the database is populated
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        code = re.sub(RE_SYMBOLES, '', chara.name_user_preferred)
    try:
        return await coupon_insert(edgedb, code=code)
    except ConstraintViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.oauth2_client_restricted.delete(
    '/coupons/{code}',
    response_model=CouponDeleteResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def delete_coupon(code: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a coupon by code."""
    resp = await coupon_delete(edgedb, code=code)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp


############
# Settings #
############
@router.oauth2.get('/settings/ranks', response_model=list[Rank])
async def get_ranks():
    """Get all ranks."""
    return list(RANKS.values())


@router.oauth2.get('/settings/rolls', response_model=list[RollData])
async def get_rolls(discord_id: int):
    """Get all rolls and their data."""
    rolls = {roll_id: roll_getter() for roll_id, roll_getter in ROLLS.items()}
    await asyncio.gather(*[roll.load(get_edgedb()) for roll in rolls.values()])
    return [
        RollData(
            id=roll_id,
            name=await roll.get_name(get_edgedb(), discord_id),
            price=await roll.get_price(get_edgedb(), discord_id),
        )
        for roll_id, roll in rolls.items()
    ]


###########
# Exports #
###########
@router.oauth2_client.get('/exports/waifus', response_model=WaifuExportResult)
async def export_waifus(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Export all waifus."""
    return await waifu_export(edgedb)


@router.oauth2.get('/exports/daily', response_model=list[MediasPoolExportResult])
async def export_daily():
    """Export daily media pool."""
    roll = TagRoll.get_daily()
    await roll.load(get_edgedb())
    assert roll.ids_al
    return await medias_pool_export(get_edgedb(), ids_al=roll.ids_al)
