from abc import ABC, abstractmethod
from .config import RL_CONFIG
from .utils import get_logger

_LOG = get_logger(__name__)

from utils import 

class DecisionEngine(ABC):
    """Strategy pattern for deciding ratelimit option"""
    def __init__(self):
        super().__init__()

    @abstractmethod
    def _set_strategy(self):
        pass

    @abstractmethod
    def allow(self, request):
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
        
        _LOG.debug("Set Token Bucket strategy")
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
    pass


class SlidingWindowLog(DecisionEngine):
    pass


class SlidingWindowCounter(DecisionEngine):
    pass


STRATEGIES = {
    "token-bucket": TokenBucket,
    "leaking-bucket": LeakingBucket,
    "fixed-window-counter": FixedWindowCounter,
    "sliding-window-log": SlidingWindowLog,
    "sliding-window-counter": SlidingWindowCounter,
}


def get_ratelimiter_instance(
    limit=RL_CONFIG["DEFAULT_LIMIT"],
    rate=RL_CONFIG["DEFAULT_RATE"],
    strategy=RL_CONFIG["DEFAULT_STRATEGY"],
):
    # TODO : validate strategy and inputs
    return STRATEGIES[strategy]()
