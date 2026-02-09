from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Union

import redis
from fastapi import FastAPI, Request
from pydantic import BaseModel
from redis.exceptions import RedisError

from hodor import async_ratelimiter, sync_ratelimiter
from hodor.config import RL_CONFIG


def _build_redis_client() -> redis.Redis:
    cfg = getattr(RL_CONFIG, "REDIS_CONFIG", {}) or {}
    return redis.Redis(
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 6379),
        db=cfg.get("db", 0),
        decode_responses=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create one client and fail fast if unreachable.
    client = _build_redis_client()
    try:
        client.ping()
    except RedisError as e:
        # Raising here prevents the API from starting in a broken state.
        raise RuntimeError("Redis unreachable during startup") from e

    app.state.redis_client = client
    try:
        yield
    finally:
        # Shutdown: gracefully close the client / pool.
        try:
            client.close()
        finally:
            try:
                client.connection_pool.disconnect()
            except Exception:
                # Best-effort shutdown; don't mask the original exception.
                pass


app = FastAPI(lifespan=lifespan)

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
@sync_ratelimiter
def read_item(item_id: int, request: Request, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/aitems/{item_id}")
@async_ratelimiter
async def read_item_async(item_id: int, request: Request, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}
