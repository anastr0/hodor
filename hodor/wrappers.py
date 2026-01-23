import asyncio
from functools import wraps

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from .config import RL_CONFIG
from .decision import DecisionEngine, STRATEGIES
from .utils import get_logger

import logging
import functools


_LOG = get_logger(__name__, logging.DEBUG)


# TODO sync wrapper
def sync_ratelimiter(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # key=None, limit=5, window=1,
        # lib doesnt know which framwork is being used
        # get args directly as kwargs
        # args = key, ratelimit = {timewindow, req count allowed per timewindow}
        request: Request = kwargs.get("request")
        limit = kwargs.get("limit", RL_CONFIG.DEFAULT_LIMIT)  # no of requests
        window = kwargs.get("window", RL_CONFIG.DEFAULT_WINDOW)  # in seconds
        strategy = kwargs.get("strategy", RL_CONFIG.DEFAULT_STRATEGY)
        key_args = (func.__name__, request.client.host)
        ratelimiter: DecisionEngine = STRATEGIES[strategy](key_args, limit, window)

        if ratelimiter.allow(key_args, limit=limit, window=window):
            return func(*args, **kwargs)
        else:
            # TODO : make this framework agnostic response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"message": "Too many requests"},
            )

    return wrapper


# TODO async wrapper - test if any issues
def async_ratelimiter(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        limit = kwargs.get("limit", RL_CONFIG.DEFAULT_LIMIT)  # no of requests
        window = kwargs.get("window", RL_CONFIG.DEFAULT_WINDOW)  # in seconds
        strategy = kwargs.get("strategy", RL_CONFIG.DEFAULT_STRATEGY)
        key_args = (func.__name__, request.client.host)
        ratelimiter: DecisionEngine = STRATEGIES[strategy](key_args, limit, window)

        if ratelimiter.allow(key_args, limit=limit, window=window):
            return await func(*args, **kwargs)
        else:
            # TODO : make this framework agnostic response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"message": "Too many requests"},
            )
    return wrapper
