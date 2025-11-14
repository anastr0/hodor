from functools import wraps

def ratelimit(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        print(args, kwargs)
        return await func(*args, **kwargs)

    return wrapper

