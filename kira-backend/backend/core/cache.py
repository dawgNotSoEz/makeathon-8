import json

import redis.asyncio as redis

from backend.core.config import config


JsonPrimitive = str | int | float | bool | None
JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]


class RedisCache:
    def __init__(self) -> None:
        self._client = redis.from_url(config.redis_url, encoding="utf-8", decode_responses=True)

    def _key(self, namespace: str, key: str) -> str:
        return f"{config.cache_namespace}:{namespace}:{key}"

    async def get_json(self, namespace: str, key: str) -> JsonValue | None:
        raw = await self._client.get(self._key(namespace, key))
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, namespace: str, key: str, value: JsonValue, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds or config.cache_ttl_seconds
        await self._client.set(self._key(namespace, key), json.dumps(value), ex=ttl)

    async def increment_with_ttl(self, namespace: str, key: str, ttl_seconds: int) -> int:
        namespaced = self._key(namespace, key)
        count = await self._client.incr(namespaced)
        if count == 1:
            await self._client.expire(namespaced, ttl_seconds)
        return count

    async def ping(self) -> bool:
        return bool(await self._client.ping())

    async def close(self) -> None:
        await self._client.close()
