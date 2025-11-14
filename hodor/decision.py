from abc import ABC, abstractmethod
from config import RL_CONFIG

class DecisionEngine(ABC):
    limit = None
    counter = None

    def __init__(self, limit=RL_CONFIG.LIMIT, counter=0):
        super().__init__()

    @abstractmethod
    def set_strategy(self):
        pass


class TokenBucket(DecisionEngine):
    pass

class LeakingBucket(DecisionEngine):
    pass

class FixedWindowCounter(DecisionEngine):
    pass

class SlidingWindowLog(DecisionEngine):
    pass

class SlidingWindowCounter(DecisionEngine):
    pass
