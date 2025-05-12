from functools import cache, cached_property
from typing import Self, cast, override
from uuid import UUID

import gel
import jwt
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request

from nanapi.database.default.client_get_by_username import (
    ClientGetByUsernameResult,
    client_get_by_username,
)
from nanapi.settings import JWT_ALGORITHM, JWT_SECRET_KEY, PROFILING
from nanapi.utils.clients import get_edgedb
from nanapi.utils.security import OAUTH2_SCHEME, japan7_basic_auth


class HTTPExceptionModel(BaseModel):
    detail: str


class NanAPIRouter(APIRouter):
    @cached_property
    def public(self) -> Self:
        return APIRouterProxy(self)  # type: ignore

    @cached_property
    def basic_auth(self) -> Self:
        return APIRouterProxy(
            self,
            dependencies=[Depends(japan7_basic_auth)],
            responses={
                status.HTTP_401_UNAUTHORIZED: dict(model=HTTPExceptionModel),
            },
        )  # type: ignore

    @cached_property
    def oauth2(self) -> Self:
        return APIRouterProxy(
            self,
            dependencies=[
                Depends(get_current_client),
            ],
            responses={
                status.HTTP_401_UNAUTHORIZED: dict(model=HTTPExceptionModel),
            },
        )  # type: ignore

    @cached_property
    def oauth2_client(self) -> Self:
        return APIRouterProxy(
            self,
            dependencies=[
                Depends(client_id_param),
                Depends(get_current_client),
            ],
            responses={
                status.HTTP_401_UNAUTHORIZED: dict(model=HTTPExceptionModel),
            },
        )  # type: ignore

    @cached_property
    def oauth2_client_restricted(self) -> Self:
        return APIRouterProxy(
            self,
            dependencies=[
                Depends(client_id_param),
                Depends(get_current_client),
                Depends(check_restricted_access),
            ],
            responses={
                status.HTTP_401_UNAUTHORIZED: dict(model=HTTPExceptionModel),
                status.HTTP_403_FORBIDDEN: dict(model=HTTPExceptionModel),
            },
        )  # type: ignore


class APIRouterProxy:
    def __init__(
        self, router: APIRouter, dependencies: list | None = None, responses: dict | None = None
    ) -> None:
        self.router = router
        self.dependencies = dependencies
        self.responses = responses

    def _prepare_kwargs(self, kwargs: dict) -> None:
        if self.dependencies:
            kwargs.setdefault('dependencies', []).extend(self.dependencies)
        if self.responses:
            kwargs.setdefault('responses', {}).update(self.responses)

    def get(self, *args, **kwargs):
        self._prepare_kwargs(kwargs)
        return self.router.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._prepare_kwargs(kwargs)
        return self.router.post(*args, **kwargs)

    def put(self, *args, **kwargs):
        self._prepare_kwargs(kwargs)
        return self.router.put(*args, **kwargs)

    def patch(self, *args, **kwargs):
        self._prepare_kwargs(kwargs)
        return self.router.patch(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._prepare_kwargs(kwargs)
        return self.router.delete(*args, **kwargs)

    def __getattr__(self, key):
        return getattr(self.router, key)


class TokenData(BaseModel):
    username: str


async def get_current_client(token: str = Depends(OAUTH2_SCHEME)) -> ClientGetByUsernameResult:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str | None = payload.get('sub', None)
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    client = await client_get_by_username(get_edgedb(), username=token_data.username)
    if client is None:
        raise credentials_exception
    return client


def client_id_param(
    client_id: UUID | None = None,
    current_client: ClientGetByUsernameResult = Depends(get_current_client),
) -> UUID:
    return client_id or current_client.id


async def check_restricted_access(
    client_id: UUID = Depends(client_id_param),
    current_client: ClientGetByUsernameResult = Depends(get_current_client),
):
    if client_id != current_client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='client_id does not match the current client',
        )


@cache
def get_client_edgedb(client_id: UUID = Depends(client_id_param)) -> gel.AsyncIOClient:
    client = get_edgedb().with_globals(client_id=client_id)
    return cast(gel.AsyncIOClient, client)


if PROFILING:
    from pyinstrument import Profiler

    class ProfilerMiddleware(BaseHTTPMiddleware):
        """https://pyinstrument.readthedocs.io/en/latest/guide.html#profile-a-web-request-in-fastapi"""

        def __init__(self, *args, fastapi_app: FastAPI | None = None, **kwargs):
            super().__init__(*args, **kwargs)
            self.results: list[tuple[str, str, str]] = []
            if fastapi_app is not None:
                router = APIRouter(prefix='/profiler', tags=['profiler'])
                router.add_api_route('/', self.list_results, response_class=HTMLResponse)
                router.add_api_route('/{id}', self.get_result, response_class=HTMLResponse)
                fastapi_app.include_router(router)

        @override
        async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
            profiler = Profiler()
            profiler.start()
            resp = await call_next(request)
            profiler.stop()
            self.results.append((request.method, str(request.url), profiler.output_html()))
            return resp

        async def list_results(self):
            li = []
            for i, (method, url, _) in enumerate(self.results):
                li.append(f'<li><a href="/profiler/{i}">{method} {url}</a></li>')
            resp = f'<ul>\n{"\n".join(reversed(li))}\n</ul>'
            return resp

        async def get_result(self, id: int):
            return self.results[id][-1]
