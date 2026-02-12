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


# TODO : deprecate wrappers in favor of using DecisionEngine directly in dependencies

def _get_redis_client_from_request(request: Request):
    redis_client = getattr(getattr(request, "app", None), "state", None)
    redis_client = getattr(redis_client, "redis_client", None)
    if redis_client is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
    return redis_client


def sync_ratelimiter(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        limit = kwargs.get("limit", RL_CONFIG.DEFAULT_LIMIT)  # no of requests
        window = kwargs.get("window", RL_CONFIG.DEFAULT_WINDOW)  # in seconds
        strategy = kwargs.get("strategy", RL_CONFIG.DEFAULT_STRATEGY)
        key_args = (func.__name__, request.client.host)
        redis_client = _get_redis_client_from_request(request)
        ratelimiter: DecisionEngine = STRATEGIES[strategy](
            limit, window, redis_client=redis_client
        )

        if ratelimiter.allow(key_args):
            return func(*args, **kwargs)
        else:
            # TODO : make this framework agnostic response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"message": "Too many requests"},
            )

    return wrapper


def async_ratelimiter(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        limit = kwargs.get("limit", RL_CONFIG.DEFAULT_LIMIT)  # no of requests
        window = kwargs.get("window", RL_CONFIG.DEFAULT_WINDOW)  # in seconds
        strategy = kwargs.get("strategy", RL_CONFIG.DEFAULT_STRATEGY)
        key_args = (func.__name__, request.client.host)

        redis_client = _get_redis_client_from_request(request)
        ratelimiter: DecisionEngine = STRATEGIES[strategy](
            limit, window, redis_client=redis_client
        )

        if ratelimiter.allow(key_args):
            return await func(*args, **kwargs)
        else:
            # TODO : make this framework agnostic response
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"message": "Too many requests"},
            )

    return wrapper
