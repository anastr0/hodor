import asyncio
from functools import wraps

from fastapi import Request, HTTPException, status
from .decision import DecisionEngine
from fastapi.responses import JSONResponse

def ratelimit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs.get("request")
        ratelimiter: DecisionEngine = kwargs.get("strategy")

        # check if request can be allowed to serve
        if ratelimiter.allow(request):
            return await func(*args, **kwargs)
        else:
            raise JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"message": "Too many requests"}
            )

    return wrapper
