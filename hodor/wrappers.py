import asyncio
from functools import wraps

from fastapi import Request, HTTPException, status
from .decision import DecisionEngine, STRATEGIES
from .utils import get_logger
from fastapi.responses import JSONResponse

import logging
import functools
import sys


_LOG = get_logger(__name__, logging.DEBUG)


def ratelimit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # TODO : avoid logic involving request, get args directly.
        # lib doesnt know what framewokr is being used
        request: Request = kwargs.get("request")
        ratelimiter: DecisionEngine = kwargs.get("strategy")

        # check if request can be allowed to serve
        if ratelimiter.allow(request):
            return await func(*args, **kwargs)
        else:
            # TODO : make this framework agnostic response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"message": "Too many requests"},
            )

    return wrapper


# TODO sync wrapper
def sync_ratelimiter(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):  # key=None, limit=5, window=1,
        # lib doesnt know which framwork is being used
        # get args directly as kwargs
        # args = key, ratelimit = {timewindow, req count allowed per timewindow}

        request: Request = kwargs.get("request")
        # if not request:
        #     # Check positional args if not in kwargs
        #     for arg in args:
        #         if isinstance(arg, Request):
        #             request = arg
        #             break
        # client_IP = request.client.host
        limit = kwargs.get("limit", 5)  # no of requests
        window = kwargs.get("window", 5)  # in seconds
        strategy = kwargs.get("strategy", "fixed-window-counter")
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
        key = kwargs.get("key")  # TODO : auto generate based on view/endpoint
        limit = kwargs.get("limit", 5)  # no of requests
        window = kwargs.get("window", 1)  # in seconds
        ratelimiter: DecisionEngine = kwargs.get("strategy", "sliding-window-counter")

        if ratelimiter.allow(key=key, limit=limit, window=window):
            return await func(*args, **kwargs)
        else:
            # TODO : make this framework agnostic response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"message": "Too many requests"},
            )

    return wrapper
