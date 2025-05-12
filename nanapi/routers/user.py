from fastapi import HTTPException, status

from nanapi.database.user.profile_get_by_discord_id import profile_get_by_discord_id
from nanapi.database.user.profile_merge_select import profile_merge_select
from nanapi.database.user.profile_select_filter_discord_id import profile_select_filter_discord_id
from nanapi.database.user.profile_select_ilike import profile_select_ilike
from nanapi.database.user.user_bulk_merge import UserBulkMergeResult, user_bulk_merge
from nanapi.database.user.user_select import UserSelectResult, user_select
from nanapi.models.user import ProfileSearchResult, UpsertDiscordAccountBodyItem, UpsertProfileBody
from nanapi.utils.clients import get_edgedb
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter

router = NanAPIRouter(prefix='/user', tags=['user'])


@router.oauth2.get('/accounts', response_model=list[UserSelectResult])
async def discord_account_index():
    """List all Discord accounts."""
    return await user_select(get_edgedb())


@router.oauth2.patch('/accounts', response_model=list[UserBulkMergeResult])
async def upsert_discord_accounts(body: list[UpsertDiscordAccountBodyItem]):
    """Bulk upsert Discord accounts."""
    return await user_bulk_merge(get_edgedb(), users=[i.model_dump() for i in body])


@router.oauth2.get('/profiles/search', response_model=list[ProfileSearchResult])
async def profile_search(discord_ids: str | None = None, pattern: str | None = None):
    """Search user profiles by Discord IDs or pattern."""
    if discord_ids is not None:
        parsed = discord_ids.split(',')
        return await profile_select_filter_discord_id(get_edgedb(), discord_ids=parsed)
    if pattern is not None:
        return await profile_select_ilike(get_edgedb(), pattern=pattern)


@router.oauth2.get(
    '/profiles/{discord_id}',
    response_model=ProfileSearchResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_profile(discord_id: str):
    """Get a user profile by Discord ID."""
    resp = await profile_get_by_discord_id(get_edgedb(), discord_id=discord_id)
    if resp is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2.patch('/profiles/{discord_id}', response_model=ProfileSearchResult)
async def upsert_profile(discord_id: str, body: UpsertProfileBody):
    """Upsert a user profile by Discord ID."""
    return await profile_merge_select(get_edgedb(), discord_id=discord_id, **body.model_dump())
