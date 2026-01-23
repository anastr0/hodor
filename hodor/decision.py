import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from .config import RL_CONFIG
from .utils import get_logger, get_redis_service

_LOG = get_logger(__name__)


class DecisionEngine(ABC):
    """Strategy pattern for deciding ratelimit option"""

    def __init__(self):
        super().__init__()

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

    def __init__(self, capacity=5, refill_rate=1):
        super().__init__()

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
    pass


class FixedWindowCounter(DecisionEngine):
    def __init__(self, *args, **kwargs):
        self.redis_client = get_redis_service()
        self._set_strategy(*args, **kwargs)
        super().__init__()

    def _set_strategy(
        self,
        key_args,
        limit=RL_CONFIG.DEFAULT_LIMIT,
        window=RL_CONFIG.DEFAULT_WINDOW,
        *args,
        **kwargs,
    ):
        """
        Docstring for _set_strategy

        :param key_args: (function_name, client_IP)
        :param limit: max requests can be allowed in given time window
        :param window: time window for ratelimiting
        """
        key_string = self.get_key_string(
            key_args
        )  # TODO-autogenerate from view function
        self.limit = limit
        self.window = window
        # window_boundary = self.get_window_boundary(window)
        # TODO create key in redis with corresponding values,
        # set expiry to window_boundary

        self.set_key(key_string=key_string, nx=True)

    def get_key_string(self, key_args):
        # TODO : create key from view/API func, for a specific user/IP
        import hashlib

        h = hashlib.md5()

        func_name = key_args[0]
        client_IP = key_args[1]
        h.update(func_name.encode("UTF-8"))
        h.update(client_IP.encode("UTF-8"))
        return h.hexdigest()

    def get_window_boundary(self, window):
        return (datetime.now() + timedelta(seconds=window)).timestamp()

    def get_value(self, key_args):
        key_string = self.get_key_string(key_args)
        return self.redis_client.hgetall(key_string)

    def set_key(
        self, key_args=None, key_string=None, expiry=None, values=None, nx=False
    ):
        # TODO : set key in redis
        window_boundary = self.get_window_boundary(self.window)
        if not expiry:
            expiry = window_boundary

        if not key_string:
            key_string = self.get_key_string(key_args)

        if nx:
            values = {
                "timestamp": window_boundary,
                "count": 1,  # how many requests allowed so far
            }
            self.redis_client.hsetnx(key_string, "timestamp", window_boundary)
            self.redis_client.hsetnx(key_string, "count", 1)
            self.redis_client.expire(key_string, 300)
        else:
            self.redis_client.hset(key_string, mapping=values)

    def get_key_value(self, key_string):
        return self.redis_client.hgetall(key_string)

    def allow(self, key_args):
        """Return true if request can be allowed
        False if ratelimit exceeded"""
        key_string = self.get_key_string(key_args)
        values = self.get_key_value(key_string)

        if not values:
            self.set_key(key_string=key_string)
            return True
        else:
            if datetime.now() < datetime.fromtimestamp(
                int(values["timestamp"].split(".")[0])
            ):
                if int(values["count"]) < self.limit:
                    values["count"] = int(values["count"]) + 1
                    self.set_key(key_string=key_string, values=values)
                    return True
                else:
                    return False
            else:
                values["timestamp"] = self.get_window_boundary(self.window)
                self.set_key(key_string=key_string, values=values)
                return True


class SlidingWindowLog(DecisionEngine):
    pass


class SlidingWindowCounter(DecisionEngine):
    """
    Implementation of Sliding Window Counter Ratelimiting Strategy
    """

    def _set_strategy(self):
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
):
    # TODO : validate strategy and inputs
    return STRATEGIES[strategy]()
