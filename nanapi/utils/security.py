import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from nanapi.database.default.client_get_by_username import (
    ClientGetByUsernameResult,
    client_get_by_username,
)
from nanapi.settings import BASIC_AUTH_PASSWORD, BASIC_AUTH_USERNAME, JWT_ALGORITHM, JWT_SECRET_KEY
from nanapi.utils.clients import get_edgedb

_pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return _pwd_context.hash(password)


_basic_auth = HTTPBasic()


def japan7_basic_auth(credentials: HTTPBasicCredentials = Depends(_basic_auth)) -> None:
    current_username_bytes = credentials.username.encode()
    correct_username_bytes = BASIC_AUTH_USERNAME.encode()
    is_correct_username = secrets.compare_digest(current_username_bytes, correct_username_bytes)
    current_password_bytes = credentials.password.encode()
    correct_password_bytes = BASIC_AUTH_PASSWORD.encode()
    is_correct_password = secrets.compare_digest(current_password_bytes, correct_password_bytes)
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Basic'},
        )


OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl='clients/token')


async def authenticate_client(username: str, password: str) -> ClientGetByUsernameResult | None:
    client = await client_get_by_username(get_edgedb(), username=username)
    if not client:
        return None
    if not verify_password(password, client.password_hash):
        return None
    return client


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update(dict(exp=expire))
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)  # pyright: ignore[reportUnknownMemberType]
    return encoded_jwt
