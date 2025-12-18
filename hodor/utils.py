# TODO : redis utils

# TODO : logger utils
import logging
import sys
import redis

def get_logger(name, level=logging.INFO):
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
    Get redis instance and return to be used
    Behaviour : Return a singleton instance, memory safe
    The instance is gracefully closed or connection pooled conns
    TODO : research how redis is used in concurrent python apps
    """

    return redis.Redis(host='hodor_cache', port=6379, db=0)

def get_postgres_connection():
    """
    Return a postgres connection
    Behaviour : To be used as context manager
    TODO : research how postgres conns are managed in concurrent python apps
    """
    pass


redis_client = get_redis_service()
postgres_connection = get_postgres_connection()
