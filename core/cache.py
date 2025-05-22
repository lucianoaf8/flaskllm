# flaskllm/core/cache.py
from __future__ import annotations

import hashlib
import json
import os
import pickle
import threading
import time
from typing import Optional, AbstractMethod

from sqlalchemy import create_engine, text

from core.config import CacheBackendType, Settings
from core.exceptions import APIError
from core.logging import get_logger

logger = get_logger(__name__)


# ---------- helpers ---------------------------------------------------------


def _sha(payload: dict) -> str:
    """Stable SHA‑256 hash used as cache key (no raw prompt stored)."""
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def build_cache_key(
    prompt: str,
    source: Optional[str],
    language: Optional[str],
    type: Optional[str],
    model: str,
) -> str:
    return _sha(
        {
            "p": prompt,
            "s": source,
            "l": language,
            "t": type,
            "m": model,
        }
    )


# ---------- backend implementations ----------------------------------------


class _BaseCache:
    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError("Subclasses must implement get()")

    def set(self, key: str, value: str, ttl: int) -> None:
        raise NotImplementedError("Subclasses must implement set()")

    def invalidate(self, key: str) -> None:
        raise NotImplementedError("Subclasses must implement invalidate()")


class _InMemoryCache(_BaseCache):
    def __init__(self, max_size: int):
        self._data: dict[str, tuple[float, str]] = {}
        self._lock = threading.Lock()
        self._max = max_size

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            exp, val = item
            if exp < time.time():
                self._data.pop(key, None)
                return None
            return val

    def set(self, key: str, value: str, ttl: int) -> None:
        with self._lock:
            if len(self._data) >= self._max:
                # simple FIFO eviction
                self._data.pop(next(iter(self._data)))
            self._data[key] = (time.time() + ttl, value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)


class _FileCache(_BaseCache):
    def __init__(self, directory: str, max_size: int):
        self.dir = directory
        self._max = max_size
        os.makedirs(self.dir, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, key: str) -> str:
        return os.path.join(self.dir, key)

    def _evict_if_needed(self):
        files = sorted((os.path.getmtime(p), p) for p in
                       (os.path.join(self.dir, f) for f in os.listdir(self.dir)))
        while len(files) > self._max:
            _, oldest = files.pop(0)
            os.remove(oldest)

    def get(self, key: str) -> Optional[str]:
        path = self._path(key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                exp, val = pickle.load(f)
            if exp < time.time():
                os.remove(path)
                return None
            return val
        except Exception:
            return None

    def set(self, key: str, value: str, ttl: int) -> None:
        path = self._path(key)
        exp = time.time() + ttl
        with self._lock:
            self._evict_if_needed()
            with open(path, "wb") as f:
                pickle.dump((exp, value), f)

    def invalidate(self, key: str) -> None:
        path = self._path(key)
        if os.path.exists(path):
            os.remove(path)


class _RedisCache(_BaseCache):
    def __init__(self, url: str):
        try:
            import redis  # noqa: D401
        except ImportError as e:
            raise APIError("Redis backend selected but redis‑py not installed") from e
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[str]:
        return self.client.get(key)

    def set(self, key: str, value: str, ttl: int) -> None:
        self.client.setex(key, ttl, value)

    def invalidate(self, key: str) -> None:
        self.client.delete(key)


class _MySQLCache(_BaseCache):
    def __init__(self, url: str):
        try:
            self.engine = create_engine(url)
        except Exception as e:
            raise APIError("Invalid MySQL URL") from e
        # ensure table exists
        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS flaskllm_cache (
                    cache_key   VARCHAR(64) PRIMARY KEY,
                    expiration  BIGINT NOT NULL,
                    value       LONGTEXT  NOT NULL
                )
            """))

    def get(self, key: str) -> Optional[str]:
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT expiration, value FROM flaskllm_cache WHERE cache_key = :k"),
                {"k": key}
            ).first()
            if not row:
                return None
            exp, val = row
            if exp < time.time():
                conn.execute(text("DELETE FROM flaskllm_cache WHERE cache_key = :k"), {"k": key})
                return None
            return val

    def set(self, key: str, value: str, ttl: int) -> None:
        exp = int(time.time() + ttl)
        with self.engine.begin() as conn:
            conn.execute(text("""
                REPLACE INTO flaskllm_cache (cache_key, expiration, value)
                VALUES (:k, :e, :v)
            """), {"k": key, "e": exp, "v": value})

    def invalidate(self, key: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM flaskllm_cache WHERE cache_key = :k"), {"k": key})


# ---------- public helpers --------------------------------------------------


def _backend(settings: Settings) -> _BaseCache:
    if settings.cache_backend == CacheBackendType.FILE:
        return _FileCache(settings.cache_dir, settings.cache_max_size)
    if settings.cache_backend == CacheBackendType.REDIS:
        return _RedisCache(settings.redis_url)
    if settings.cache_backend == CacheBackendType.MYSQL:
        if not settings.mysql_url:
            raise APIError("MySQL cache selected but mysql_url not set")
        return _MySQLCache(settings.mysql_url)
    return _InMemoryCache(settings.cache_max_size)


def get_cache(settings: Settings) -> _BaseCache:
    return _backend(settings)


class CachedLLMHandler:
    """Transparent wrapper that injects caching around any LLMHandler."""

    def __init__(self, handler, settings: Settings):
        self._handler = handler
        self._settings = settings
        self._cache = get_cache(settings)

    # keep identical signature
    def process_prompt(
        self,
        prompt: str,
        source: Optional[str] = None,
        language: Optional[str] = None,
        type: Optional[str] = None,
    ) -> str:
        if not self._settings.cache_enabled:
            return self._handler.process_prompt(prompt, source, language, type)

        key = build_cache_key(prompt, source, language, type, getattr(self._handler, "model", ""))
        try:
            cached = self._cache.get(key)
            if cached is not None:
                logger.info("cache_hit", key=key)
                return cached
            logger.info("cache_miss", key=key)
        except Exception as ce:  # cache failure should NOT break the request
            logger.error("cache_error_get", error=str(ce))

        result = self._handler.process_prompt(prompt, source, language, type)

        try:
            self._cache.set(key, result, self._settings.cache_expiration)
        except Exception as ce:
            logger.error("cache_error_set", error=str(ce))

        return result
