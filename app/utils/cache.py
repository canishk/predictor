import hashlib
import json
from typing import Any

from cachetools import TTLCache

from app.config import get_settings


class TTLResponseCache:
    def __init__(self) -> None:
        settings = get_settings()
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=512, ttl=settings.cache_ttl_seconds)

    def _key(self, namespace: str, *parts: Any) -> str:
        raw = json.dumps([namespace, *parts], sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, namespace: str, *parts: Any) -> Any | None:
        return self._cache.get(self._key(namespace, *parts))

    def set(self, namespace: str, value: Any, *parts: Any) -> None:
        self._cache[self._key(namespace, *parts)] = value

    def clear(self) -> None:
        self._cache.clear()


cache = TTLResponseCache()
