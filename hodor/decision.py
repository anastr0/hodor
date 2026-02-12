import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import redis
from redis.exceptions import ResponseError

from .config import RL_CONFIG
from .utils import get_logger

_LOG = get_logger(__name__)

# -----------------------------------------------------------------------------
# Lua script: atomic fixed-window rate limit (single round-trip, no races)
# -----------------------------------------------------------------------------
# Runs entirely inside Redis so concurrent requests from multiple instances
# for the same key are serialized and never see a stale read or double-increment.
#
# KEYS[1]: rate-limit key (e.g. hash of endpoint + client IP)
# ARGV[1]: limit (max requests per window)
# ARGV[2]: window_end_ts (end of current window as Unix timestamp)
# ARGV[3]: ttl_seconds (key expiry, e.g. 300)
# ARGV[4]: current_time (current time as Unix timestamp)
#
# Returns: 1 = allow, 0 = rate limit exceeded
#
# Logic:
#   - If key missing or stored window has ended: set new window, count=1, allow.
#   - Else if count < limit: increment count, allow.
#   - Else: deny.
# -----------------------------------------------------------------------------
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

# SHA1 of script for EVALSHA (one round-trip, script not sent each time).
_FIXED_WINDOW_SCRIPT_SHA = hashlib.sha1(
    FIXED_WINDOW_ATOMIC_SCRIPT.encode()
).hexdigest()


def register_rate_limit_scripts(redis_client):
    """
    Load Lua scripts into Redis so EVALSHA works without sending the script body.
    Call once at app startup (e.g. FastAPI lifespan) after the Redis client is ready.
    """
    _LOG.debug("Registering rate limit scripts in Redis.")
    redis_client.script_load(FIXED_WINDOW_ATOMIC_SCRIPT)
    _LOG.debug("Rate limit scripts registered successfully.")


def _fixed_window_allow(redis_client, key_string, limit, window_end, ttl):
    """
    Run the fixed-window Lua script atomically.
    Uses EVALSHA when the script is cached in Redis; falls back to EVAL on NOSCRIPT.
    Returns True if the request is allowed, False if rate limited.
    """
    current_time = datetime.now().timestamp()
    _LOG.debug(
        "Attempting to allow request with key: %s, limit: %d, window_end: %f, ttl: %d, current_time: %f",
        key_string, limit, window_end, ttl, current_time
    )
    try:
        result = redis_client.evalsha(
            _FIXED_WINDOW_SCRIPT_SHA, 1, key_string, limit, window_end, ttl, current_time
        )
        _LOG.debug("EVALSHA executed successfully for key: %s", key_string)
    except ResponseError as e:
        if "NOSCRIPT" not in str(e):
            _LOG.error("Redis ResponseError: %s", str(e))
            raise
        _LOG.debug("Script not cached in Redis. Falling back to EVAL for key: %s", key_string)
        result = redis_client.eval(
            FIXED_WINDOW_ATOMIC_SCRIPT, 1, key_string, limit, window_end, ttl, current_time
        )
        _LOG.debug("EVAL executed successfully for key: %s", key_string)

    allowed = result == 1
    if allowed:
        _LOG.debug("Request allowed for key: %s", key_string)
    else:
        _LOG.debug("Rate limit exceeded for key: %s", key_string)
    return allowed


class DecisionEngine(ABC):
    """Strategy pattern for deciding ratelimit option"""

    def __init__(self, redis_client=None):
        super().__init__()
        self.redis_client = redis_client

    @abstractmethod
    def _set_strategy(self):
        pass

    @abstractmethod
    def allow(self, *args, **kwargs):
        """Return true if request can be allowed
        False if ratelimit exceeded"""
        pass


class TokenBucket(DecisionEngine):
    BUCKET_CAPACITY = 5  # maximum number of tokens bucket can hold
    TOKEN_REFILL_RATE = 1  # tokens added per second to bucket

    def __init__(
        self,
        key_args=None,
        limit=RL_CONFIG.DEFAULT_LIMIT,
        window=RL_CONFIG.DEFAULT_WINDOW,
        capacity=5,
        refill_rate=1,
        redis_client=None,
        *args,
        **kwargs,
    ):
        super().__init__(redis_client=redis_client)

    def _set_strategy(self):
        # TODO : init token bucket specific params
        # TODO : set token bucket capacity and refill rate
        self.curr_capacity = 0

        return super()._set_strategy()

    def allow(self, request):
        # TODO : token bucket specific allow logic
        return super().allow(request)

    def _refill_tokens(self):
        # TODO : logic to refill tokens based on time elapsed
        pass


class LeakingBucket(DecisionEngine):
    def __init__(
        self,
        key_args=None,
        limit=RL_CONFIG.DEFAULT_LIMIT,
        window=RL_CONFIG.DEFAULT_WINDOW,
        redis_client=None,
        *args,
        **kwargs,
    ):
        super().__init__(redis_client=redis_client)


class FixedWindowCounter(DecisionEngine):
    def __init__(
        self,
        key_args,
        limit=RL_CONFIG.DEFAULT_LIMIT,
        window=RL_CONFIG.DEFAULT_WINDOW,
        redis_client=None,
        *args,
        **kwargs,
    ):
        super().__init__(redis_client=redis_client)
        self._set_strategy(key_args, limit, window, *args, **kwargs)

    def _set_strategy(
        self,
        key_args,
        limit=RL_CONFIG.DEFAULT_LIMIT,
        window=RL_CONFIG.DEFAULT_WINDOW,
        *args,
        **kwargs,
    ):
        """
        :param key_args: (function_name, client_IP)
        :param limit: max requests allowed in the time window
        :param window: time window in seconds for rate limiting
        """
        self.limit = limit
        self.window = window
        # Key is created atomically on first allow() via Lua script; no init here
        # to avoid races when multiple instances receive the first request.

    def _key_string(self, key_args):
        """Stable key for this (endpoint, client) pair; one hash call."""
        func_name, client_ip = key_args[0], key_args[1]
        payload = f"{func_name}:{client_ip}".encode("utf-8")
        return hashlib.md5(payload).hexdigest()

    def _window_end_ts(self, window_seconds):
        """Unix timestamp of the current window end (now + window)."""
        return (datetime.now() + timedelta(seconds=window_seconds)).timestamp()

    def get_key_string(self, key_args):
        """Public alias for _key_string (tests / legacy)."""
        return self._key_string(key_args)

    def get_window_boundary(self, window):
        """Public alias for _window_end_ts (legacy set_key)."""
        return self._window_end_ts(window)

    # --- Legacy / debug (racy if used for rate decisions; use allow() instead) ---
    def get_value(self, key_args):
        return self.redis_client.hgetall(self.get_key_string(key_args))

    def get_key_value(self, key_string):
        return self.redis_client.hgetall(key_string)

    def set_key(
        self, key_args=None, key_string=None, expiry=None, values=None, nx=False
    ):
        window_boundary = self.get_window_boundary(self.window)
        expiry = expiry or window_boundary
        key_string = key_string or self.get_key_string(key_args)

        if nx:
            # Only set if key doesn't exist. Not atomic with get, but useful for testing / debug.
            pipeline = self.redis_client.pipeline(transaction=False)
            pipeline.hsetnx(key_string, "timestamp", window_boundary)
            pipeline.hsetnx(key_string, "count", 1)
            pipeline.expire(key_string, FIXED_WINDOW_KEY_TTL)
            pipeline.execute()
        else:
            values = values or {
                "timestamp": window_boundary,
                "count": 1,
            }
            pipeline = self.redis_client.pipeline(transaction=False)
            pipeline.hset(key_string, mapping=values)
            pipeline.expire(key_string, FIXED_WINDOW_KEY_TTL)
            pipeline.execute()

    def allow(self, key_args):
        """
        Decide if the request is allowed under the fixed-window limit.
        Single Redis round-trip via EVALSHA (or EVAL on NOSCRIPT); atomic, no races.
        """
        key_string = self._key_string(key_args)
        window_end = self._window_end_ts(self.window)
        _LOG.debug(
            "Checking rate limit for key: %s with window_end: %f", key_string, window_end
        )
        allowed = _fixed_window_allow(
            self.redis_client,
            key_string,
            self.limit,
            window_end,
            FIXED_WINDOW_KEY_TTL,
        )
        if allowed:
            _LOG.debug("Request allowed for key: %s", key_string)
        else:
            _LOG.debug("Request denied for key: %s due to rate limit.", key_string)
        return allowed


class SlidingWindowLog(DecisionEngine):
    def __init__(
        self,
        key_args=None,
        limit=RL_CONFIG.DEFAULT_LIMIT,
        window=RL_CONFIG.DEFAULT_WINDOW,
        redis_client=None,
        *args,
        **kwargs,
    ):
        super().__init__(redis_client=redis_client)


class SlidingWindowCounter(DecisionEngine):
    """
    Implementation of Sliding Window Counter Ratelimiting Strategy
    """

    def __init__(
        self,
        key_args=None,
        limit=RL_CONFIG.DEFAULT_LIMIT,
        window=RL_CONFIG.DEFAULT_WINDOW,
        redis_client=None,
        *args,
        **kwargs,
    ):
        super().__init__(redis_client=redis_client)
        self._set_strategy(key_args, limit, window, *args, **kwargs)

    def _set_strategy(self, *args, **kwargs):
        return super()._set_strategy()

    def allow(self, request):
        return super().allow(request)


STRATEGIES = {
    "token-bucket": TokenBucket,
    "leaking-bucket": LeakingBucket,
    "fixed-window-counter": FixedWindowCounter,
    "sliding-window-log": SlidingWindowLog,
    "sliding-window-counter": SlidingWindowCounter,
}


def get_ratelimiter_instance(
    limit=RL_CONFIG.DEFAULT_LIMIT,
    window=RL_CONFIG.DEFAULT_WINDOW,
    strategy=RL_CONFIG.DEFAULT_STRATEGY,
    redis_client=None,
):
    # TODO : validate strategy and inputs
    return STRATEGIES[strategy](None, limit, window, redis_client=redis_client)
