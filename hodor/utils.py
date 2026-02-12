import logging
import sys


def get_logger(name, level=logging.DEBUG):
    """
    Return a module logger configured to write to stdout.
    Safe to call multiple times from different modules — handlers are only added once.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Add a single StreamHandler to stdout if none exist
    if not any(
        isinstance(h, logging.StreamHandler)
        and getattr(h, "stream", None) is sys.stdout
        for h in logger.handlers
    ):
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)

    return logger


def get_redis_service():
    """
    Legacy helper for creating a Redis client.

    Prefer creating exactly one client during the FastAPI app lifespan
    and injecting it (e.g. via request.app.state.redis_client).
    """
    import redis

    return redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
