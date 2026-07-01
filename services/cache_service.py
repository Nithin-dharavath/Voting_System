import json
import logging
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

_redis: Any = None


def get_redis() -> Any | None:
    global _redis
    if _redis is None:
        try:
            from redis import Redis

            _redis = Redis.from_url(settings.redis_url, decode_responses=True)
            _redis.ping()
        except ImportError:
            logger.info("redis package not installed. Caching disabled.")
            _redis = None
        except Exception:
            logger.warning("Redis is not available. Caching disabled.")
            _redis = None
    return _redis


def cache_get(key: str) -> Any | None:
    r = get_redis()
    if r is None:
        return None
    try:
        data = r.get(key)
        if data is None:
            return None
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    except Exception:
        logger.exception("Redis cache_get failed for key: %s", key)
        return None


def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        if isinstance(value, dict | list | tuple | bool | int | float):
            data = json.dumps(value, default=str)
        else:
            data = str(value)
        r.setex(key, ttl, data)
    except Exception:
        logger.exception("Redis cache_set failed for key: %s", key)


def cache_delete(key: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        r.delete(key)
    except Exception:
        logger.exception("Redis cache_delete failed for key: %s", key)


def cache_delete_prefix(prefix: str) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        for key in r.scan_iter(match=f"{prefix}*"):
            r.delete(key)
    except Exception:
        logger.exception("Redis cache_delete_prefix failed for prefix: %s", prefix)
