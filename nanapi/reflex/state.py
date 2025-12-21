from typing import TYPE_CHECKING, cast

import gel
import reflex as rx

from nanapi.settings import EDGEDB_CONFIG


class BaseState(rx.State):
    if TYPE_CHECKING:
        client_id: str

    @property
    def _global_executor(self) -> gel.AsyncIOClient:
        client = gel.create_async_client(**EDGEDB_CONFIG)
        return client

    @property
    def _client_executor(self) -> gel.AsyncIOClient | None:
        if not self.client_id:
            return
        client = self._global_executor.with_globals(client_id=self.client_id)
        return cast(gel.AsyncIOClient, client)
