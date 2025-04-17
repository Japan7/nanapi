from fastapi import Depends, HTTPException, Response, status
from gel import AsyncIOClient
from gel.errors import ConstraintViolationError

from nanapi.database.role.role_delete_by_role_id import (
    RoleDeleteByRoleIdResult,
    role_delete_by_role_id,
)
from nanapi.database.role.role_insert_select import RoleInsertSelectResult, role_insert_select
from nanapi.database.role.role_select_all import RoleSelectAllResult, role_select_all
from nanapi.models.role import NewRoleBody
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/roles', tags=['role'])


@router.oauth2_client.get('/', response_model=list[RoleSelectAllResult])
async def get_roles(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get all roles."""
    return await role_select_all(edgedb)


@router.oauth2_client_restricted.post(
    '/',
    response_model=RoleInsertSelectResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel)},
)
async def new_role(body: NewRoleBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Create a new role."""
    try:
        return await role_insert_select(edgedb, **body.model_dump())
    except ConstraintViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.oauth2_client_restricted.delete(
    '/{role_id}',
    response_model=RoleDeleteByRoleIdResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def delete_role(role_id: int, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a role by role_id."""
    resp = await role_delete_by_role_id(edgedb, role_id=role_id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp
