from fastapi import Depends, HTTPException, status
from gel import AsyncIOClient

from nanapi.database.pot.pot_add import PotAddResult, pot_add
from nanapi.database.pot.pot_get_by_user import PotGetByUserResult, pot_get_by_user
from nanapi.models.pot import CollectPotBody
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/pots', tags=['pot'])


@router.oauth2_client.get(
    '/{discord_id}',
    response_model=PotGetByUserResult,
    responses={status.HTTP_404_NOT_FOUND: dict(model=HTTPExceptionModel)},
)
async def get_pot(discord_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    resp = await pot_get_by_user(edgedb, discord_id=discord_id)
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.post('/{discord_id}', response_model=PotAddResult)
async def collect_pot(
    discord_id: int, body: CollectPotBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)
):
    return await pot_add(edgedb, discord_id=discord_id, **body.model_dump())
