from uuid import UUID

from fastapi import Depends, Response, status
from gel import AsyncIOClient

from nanapi.database.ai.skill_delete_by_id import SkillDeleteByIdResult, skill_delete_by_id
from nanapi.database.ai.skill_insert import SkillInsertResult, skill_insert
from nanapi.database.ai.skill_select_all import SkillSelectAllResult, skill_select_all
from nanapi.models.ai import InsertSkillBody
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/ai', tags=['ai'])


@router.oauth2_client.get('/skills', response_model=list[SkillSelectAllResult])
async def skill_index(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """List all skills."""
    return await skill_select_all(edgedb)


@router.oauth2_client_restricted.post('/skills', response_model=SkillInsertResult)
async def insert_skill(body: InsertSkillBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Insert a new skill."""
    return await skill_insert(edgedb, **body.model_dump())


@router.oauth2_client_restricted.delete(
    '/skills/{id}',
    response_model=SkillDeleteByIdResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def delete_skill(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a skill."""
    resp = await skill_delete_by_id(edgedb, id=id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp
