import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

import orjson
from gel import AsyncIOExecutor

from nanapi.database.redis.data_delete_by_key import data_delete_by_key
from nanapi.database.redis.data_get_by_key import DataGetByKeyResult, data_get_by_key
from nanapi.database.redis.data_merge import data_merge
from nanapi.database.redis.data_select_key_ilike import data_select_key_ilike
from nanapi.settings import INSTANCE_NAME
from nanapi.utils.clients import get_edgedb

logger = logging.getLogger(__name__)


def make_redis_key(key: str):
    return f'{INSTANCE_NAME}_{key}'


T = TypeVar('T')


class BaseRedis(ABC, Generic[T]):
    key: str

    def __init__(self, key: str, global_key: bool = False):
        self.key = key if global_key else make_redis_key(key)

    async def get(
        self, sub_key: str | int | None = None, tx: AsyncIOExecutor | None = None
    ) -> T | None:
        key = self.key if sub_key is None else f'{self.key}:{sub_key}'
        try:
            if tx is None:
                tx = get_edgedb()

            resp = await data_get_by_key(tx, key=key)
            return self._decode(resp)
        except Exception as e:
            logger.exception(e)
            return

    async def set(
        self,
        value: T,
        sub_key: str | int | None = None,
        tx: AsyncIOExecutor | None = None,
    ):
        key = self.key if sub_key is None else f'{self.key}:{sub_key}'
        encoded_value = self.encode(value)
        try:
            if tx is None:
                tx = get_edgedb()

            await data_merge(tx, key=key, value=encoded_value)
        except Exception as e:
            logger.exception(e)
            return

    async def delete(self, sub_key: str | int | None = None, tx: AsyncIOExecutor | None = None):
        key = self.key if sub_key is None else f'{self.key}:{sub_key}'

        if tx is None:
            tx = get_edgedb()

        await data_delete_by_key(tx, key=key)

    async def get_all(self, tx: AsyncIOExecutor | None = None):
        if tx is None:
            tx = get_edgedb()

        resp = await data_select_key_ilike(tx, pattern=f'{self.key}:%')
        for item in resp:
            *_, sub_key = item.key.rpartition(':')
            yield sub_key, await self.get(sub_key)

    @abstractmethod
    def encode(self, value: T) -> str: ...

    def _decode(self, resp: DataGetByKeyResult | None) -> T | None:
        if resp is None:
            return None
        return self.decode(resp.value)

    @abstractmethod
    def decode(self, value: str) -> T: ...


class StringValue(BaseRedis[str]):
    def encode(self, value: str) -> str:
        return value

    def decode(self, value: str) -> str:
        return value


class _IntegerValueMixin:
    def encode(self, value: int) -> str:
        return str(value)

    def decode(self, value: str) -> int:
        return int(value)


class IntegerValue(_IntegerValueMixin, BaseRedis[int]):
    pass


class FloatValue(BaseRedis[float]):
    def encode(self, value: float) -> str:
        return str(value)

    def decode(self, value: str) -> float:
        return float(value)


class BooleanValue(_IntegerValueMixin, BaseRedis[bool]):
    def __init__(self, key: str, global_key: bool = False, default: bool = False):
        super().__init__(key, global_key)
        self.default = default

    def encode(self, value: int | bool) -> str:
        return super().encode(int(value))

    def decode(self, value: str) -> bool:
        return bool(super().decode(value))

    def _decode(self, resp: DataGetByKeyResult | None):
        if resp is None:
            return self.default
        return super()._decode(resp)


class JSONValue(BaseRedis[Any]):
    def __init__(self, key: str, global_key: bool = False, **orjson_kwargs: Any):
        super().__init__(key, global_key)
        self.orjson_kwargs = orjson_kwargs

    def encode(self, value: Any) -> str:
        return orjson.dumps(value, **self.orjson_kwargs).decode()

    def decode(self, value: str) -> Any:
        return orjson.loads(value)
