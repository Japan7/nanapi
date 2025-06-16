from fastapi import Depends, HTTPException, Response, status
from gel import AsyncIOClient

from nanapi.database.ai.prompt_delete import PromptDeleteResult, prompt_delete
from nanapi.database.ai.prompt_insert import PromptInsertResult, prompt_insert
from nanapi.database.ai.prompt_select_by_name import (
    PromptSelectByNameResult,
    prompt_select_by_name,
)
from nanapi.database.ai.prompt_select_name_desc import (
    PromptSelectNameDescResult,
    prompt_select_name_desc,
)
from nanapi.models.ai import InsertPromptBody
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/ai', tags=['ai'])


@router.oauth2_client.get('/prompts', response_model=list[PromptSelectNameDescResult])
async def prompt_index(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """List all prompts (name and description)."""
    return await prompt_select_name_desc(edgedb)


@router.oauth2_client_restricted.post('/prompts', response_model=PromptInsertResult)
async def insert_prompt(
    body: InsertPromptBody,
    edgedb: AsyncIOClient = Depends(get_client_edgedb),
):
    """Insert a new prompt."""
    return await prompt_insert(
        edgedb,
        name=body.name,
        description=body.description,
        prompt=body.prompt,
        arguments=[a.model_dump_json() for a in body.arguments],
    )


@router.oauth2_client.get(
    '/prompts/{name}',
    response_model=PromptSelectByNameResult,
    responses={status.HTTP_404_NOT_FOUND: {}},
)
async def get_prompt(name: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get a prompt by name."""
    resp = await prompt_select_by_name(edgedb, name=name)
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return resp


@router.oauth2_client_restricted.delete(
    '/prompts/{name}',
    response_model=PromptDeleteResult,
    responses={status.HTTP_204_NO_CONTENT: {}},
)
async def delete_prompt(name: str, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a prompt by name."""
    resp = await prompt_delete(edgedb, name=name)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp
