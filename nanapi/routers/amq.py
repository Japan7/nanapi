from edgedb import AsyncIOClient
from fastapi import Depends

from nanapi.database.amq.account_merge import AccountMergeResult, account_merge
from nanapi.database.amq.account_select import AccountSelectResult, account_select
from nanapi.database.amq.settings_merge import SettingsMergeResult, settings_merge
from nanapi.database.amq.settings_select_all import SettingsSelectAllResult, settings_select_all
from nanapi.models.amq import UpdateAMQSettingsBody, UpsertAMQAccountBody
from nanapi.utils.clients import get_edgedb
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/amq', tags=['amq'])


@router.oauth2.get('/accounts', response_model=list[AccountSelectResult])
async def get_accounts(username: str | None = None):
    return await account_select(get_edgedb(), username=username)


@router.oauth2.patch('/accounts/{discord_id}',
                     response_model=AccountMergeResult)
async def upsert_account(discord_id: int, body: UpsertAMQAccountBody):
    return await account_merge(get_edgedb(),
                               discord_id=discord_id,
                               **body.dict())


@router.oauth2_client.get('/settings',
                          response_model=list[SettingsSelectAllResult])
async def get_settings(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    return await settings_select_all(edgedb)


@router.oauth2_client_restricted.patch('/settings',
                                       response_model=list[SettingsMergeResult])
async def update_settings(body: UpdateAMQSettingsBody,
                          edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    return await settings_merge(edgedb, **body.dict())
