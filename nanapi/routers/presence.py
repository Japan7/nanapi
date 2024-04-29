from uuid import UUID

from edgedb import AsyncIOClient
from edgedb.errors import ConstraintViolationError
from fastapi import Depends, HTTPException, Response, status

from nanapi.database.presence.presence_delete_by_id import (
    PresenceDeleteByIdResult,
    presence_delete_by_id,
)
from nanapi.database.presence.presence_insert import PresenceInsertResult, presence_insert
from nanapi.database.presence.presence_select_all import (
    PresenceSelectAllResult,
    presence_select_all,
)
from nanapi.models.presence import NewPresenceBody
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/presences', tags=['presence'])


@router.oauth2_client.get('/', response_model=list[PresenceSelectAllResult])
async def get_presences(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    return await presence_select_all(edgedb)


@router.oauth2_client_restricted.post(
    '/',
    response_model=PresenceInsertResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel)})
async def new_presence(body: NewPresenceBody,
                       edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    try:
        return await presence_insert(edgedb, **body.model_dump())
    except ConstraintViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.oauth2_client_restricted.delete(
    '/{id}',
    response_model=PresenceDeleteByIdResult,
    responses={status.HTTP_204_NO_CONTENT: {}})
async def delete_presence(id: UUID,
                          edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    resp = await presence_delete_by_id(edgedb, id=id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp
