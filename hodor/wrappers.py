import asyncio
from functools import wraps

from fastapi import Request, HTTPException, status
from .decision import DecisionEngine


def ratelimit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        ratelimiter: DecisionEngine = kwargs.get("strategy")

        # check if request can be allowed to serve
        if ratelimiter.allow(request):
            return await func(*args, **kwargs)

        raise HTTPException(status_code=429)

    return wrapper
