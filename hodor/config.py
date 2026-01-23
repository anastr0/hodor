
TEMP_ENV_CONFIG = {
    "LIMIT": 0,
    "DEFAULT_MAX_REQUESTS": 5,  # 10 reqs/sec
    "DEFAULT_TIME_INTERVAL": 10,  # 1 sec
    "DEFAULT_STRATEGY": "fixed-window-counter",
    "REDIS_CONFIG": {
        "host": "localhost",
        "port": 6379,
        "db": 0,
    }
}  ## TODO : replace with environ obj


class HodorConfig:
    def __init__(self, DEFAULT_MAX_REQUESTS: int, DEFAULT_TIME_INTERVAL: int, REDIS_CONFIG: dict, DEFAULT_RATE_LIMITER_STRATEGY="fixed-window-counter",  **kwargs):
        self.DEFAULT_LIMIT = DEFAULT_MAX_REQUESTS
        self.DEFAULT_WINDOW = DEFAULT_TIME_INTERVAL
        self.DEFAULT_STRATEGY = DEFAULT_RATE_LIMITER_STRATEGY

        self.REDIS_CONFIG = REDIS_CONFIG


RL_CONFIG = HodorConfig(**TEMP_ENV_CONFIG)
