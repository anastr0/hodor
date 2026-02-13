import os
from typing import Any, Callable

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: Any = None, coerce: Callable[[str], Any] = lambda x: x) -> Any:
    """Read env var; apply coerce and return default if unset or empty."""
    raw = os.getenv(key)
    if raw is None or raw == "":
        return default
    return coerce(raw)


def _load_redis_config() -> dict[str, Any]:
    return {
        "host": _env("REDIS_HOST", "localhost"),
        "port": _env("REDIS_PORT", 6379, int),
        "db": _env("REDIS_DB", 0, int),
    }


def _load_hodor_config() -> dict[str, Any]:
    return {
        "DEFAULT_MAX_REQUESTS": _env("HODOR_DEFAULT_MAX_REQUESTS", 5, int),
        "DEFAULT_TIME_INTERVAL": _env("HODOR_DEFAULT_TIME_INTERVAL", 10, int),
        "DEFAULT_RATE_LIMITER_STRATEGY": _env("HODOR_DEFAULT_STRATEGY", "fixed-window-counter"),
        "REDIS_CONFIG": _load_redis_config(),
    }

FIXED_WINDOW_ATOMIC_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window_end = tonumber(ARGV[2])
local ttl = tonumber(ARGV[3])
local current_time = tonumber(ARGV[4])

local ts = redis.call('HGET', key, 'timestamp')
local cnt = redis.call('HGET', key, 'count')

if ts == false or ts == nil then
  redis.call('HSET', key, 'timestamp', window_end, 'count', 1)
  redis.call('EXPIRE', key, ttl)
  return 1
end

if tonumber(ts) <= current_time then
  redis.call('HSET', key, 'timestamp', window_end, 'count', 1)
  redis.call('EXPIRE', key, ttl)
  return 1
end

local count = tonumber(cnt or 0)
if count < limit then
  redis.call('HINCRBY', key, 'count', 1)
  redis.call('EXPIRE', key, ttl)
  return 1
end

return 0
"""
# TTL for the rate-limit key (seconds). Should be >= window to avoid early expiry.
FIXED_WINDOW_KEY_TTL = 300


class HodorConfig:
    def __init__(
        self,
        DEFAULT_MAX_REQUESTS: int,
        DEFAULT_TIME_INTERVAL: int,
        REDIS_CONFIG: dict,
        DEFAULT_RATE_LIMITER_STRATEGY="fixed-window-counter",
        **kwargs,
    ):
        self.DEFAULT_LIMIT = DEFAULT_MAX_REQUESTS
        self.DEFAULT_WINDOW = DEFAULT_TIME_INTERVAL
        self.DEFAULT_STRATEGY = DEFAULT_RATE_LIMITER_STRATEGY

        self.REDIS_CONFIG = REDIS_CONFIG


RL_CONFIG = HodorConfig(**_load_hodor_config())
