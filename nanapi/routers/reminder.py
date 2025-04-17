from uuid import UUID

from fastapi import Depends, Response, status
from gel import AsyncIOClient

from nanapi.database.reminder.reminder_delete_by_id import (
    ReminderDeleteByIdResult,
    reminder_delete_by_id,
)
from nanapi.database.reminder.reminder_insert_select import (
    ReminderInsertSelectResult,
    reminder_insert_select,
)
from nanapi.database.reminder.reminder_select_all import (
    ReminderSelectAllResult,
    reminder_select_all,
)
from nanapi.models.reminder import NewReminderBody
from nanapi.utils.fastapi import NanAPIRouter, get_client_edgedb

router = NanAPIRouter(prefix='/reminders', tags=['reminder'])


@router.oauth2_client.get('/', response_model=list[ReminderSelectAllResult])
async def get_reminders(edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Get all reminders."""
    return await reminder_select_all(edgedb)


@router.oauth2_client_restricted.post(
    '/', response_model=ReminderInsertSelectResult, status_code=status.HTTP_201_CREATED
)
async def new_reminder(body: NewReminderBody, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Create a new reminder."""
    return await reminder_insert_select(edgedb, **body.model_dump())


@router.oauth2_client_restricted.delete(
    '/{id}', response_model=ReminderDeleteByIdResult, responses={status.HTTP_204_NO_CONTENT: {}}
)
async def delete_reminder(id: UUID, edgedb: AsyncIOClient = Depends(get_client_edgedb)):
    """Delete a reminder by ID."""
    resp = await reminder_delete_by_id(edgedb, id=id)
    if resp is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return resp
