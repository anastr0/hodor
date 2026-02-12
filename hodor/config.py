TEMP_ENV_CONFIG = {
    "LIMIT": 0,
    "DEFAULT_MAX_REQUESTS": 1,  # 10 reqs/sec
    "DEFAULT_TIME_INTERVAL": 5,  # 1 sec
    "DEFAULT_STRATEGY": "fixed-window-counter",
    "REDIS_CONFIG": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
    },
}  ## TODO : replace with environ obj

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


RL_CONFIG = HodorConfig(**TEMP_ENV_CONFIG)
