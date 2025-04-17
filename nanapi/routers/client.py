from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from gel import ConstraintViolationError

from nanapi.database.default.client_get_by_username import ClientGetByUsernameResult
from nanapi.database.default.client_insert import ClientInsertResult, client_insert
from nanapi.models.client import LoginResponse, NewClientBody, WhoamiResponse
from nanapi.settings import JWT_EXPIRE_MINUTES
from nanapi.utils.clients import get_edgedb
from nanapi.utils.fastapi import HTTPExceptionModel, NanAPIRouter, get_current_client
from nanapi.utils.security import authenticate_client, create_access_token, get_password_hash

router = NanAPIRouter(prefix='/clients', tags=['client'])


@router.oauth2_client.get('/', response_model=WhoamiResponse)
async def whoami(current_user: ClientGetByUsernameResult = Depends(get_current_client)):
    """Get information about the currently authenticated client."""
    return current_user


@router.basic_auth.post(
    '/',
    response_model=ClientInsertResult,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: dict(model=HTTPExceptionModel)},
)
async def register(body: NewClientBody):
    """Register a new client account."""
    password = body.password
    password_hash = get_password_hash(password)
    try:
        return await client_insert(
            get_edgedb(), username=body.username, password_hash=password_hash
        )
    except ConstraintViolationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.public.post(
    '/token',
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_401_UNAUTHORIZED: dict(model=HTTPExceptionModel)},
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate client and return JWT access token."""
    client = await authenticate_client(form_data.username, form_data.password)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=dict(sub=client.username), expires_delta=access_token_expires
    )
    return dict(token_type='bearer', access_token=access_token)
