from abc import ABC, abstractmethod
from .config import RL_CONFIG


class DecisionEngine(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def set_strategy(self):
        pass


class TokenBucket(DecisionEngine):
    BUCKET_CAPACITY = 5  # maximum number of tokens bucket can hold
    TOKEN_REFILL_RATE = 1  # tokens added per second to bucket

    def __init__(self, capacity=5, refill_rate=1):
        super().__init__()


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
