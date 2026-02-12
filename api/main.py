from __future__ import annotations

from contextlib import asynccontextmanager
import socket
from typing import Union

import redis
from fastapi import Depends, FastAPI, Request
from pydantic import BaseModel
from redis.exceptions import RedisError

from hodor.config import RL_CONFIG
from hodor.decision import FixedWindowCounter, register_rate_limit_scripts


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
    register_rate_limit_scripts(client)
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


app = FastAPI(lifespan=lifespan, root_path="/api/v1/hodor")


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


@app.get("/")
def read_root():
    return {
        "Container ID": socket.gethostname(),
        "Title": "Test different rate limit strategies with FastAPI and Redis in a distributed setting",
        "Description": "This is a sample API to test different rate limit strategies with FastAPI and Redis. You can use the /items/{item_id} endpoint to test the rate limit.",
        "Endpoints": {
            "/fixed": "Fixed rate limit of 5 requests per second",
            "/sliding": "Sliding window rate limit of 5 requests per second",
            "/token": "Token bucket rate limit of 5 requests per second",
        },
    }


@app.get(
    "/fixed",
    dependencies=[
        Depends(
            FixedWindowCounter(
                limit=RL_CONFIG.DEFAULT_LIMIT, window=RL_CONFIG.DEFAULT_WINDOW
            )
        )
    ],
)
def read_item(request: Request):
    return {"message": "This endpoint uses fixed window rate limiting"}


@app.get("/sliding")
def create_item(request: Request):
    return {"message": "This endpoint uses sliding window rate limiting"}


@app.get("/token")
def update_item(request: Request):
    return {"message": "This endpoint uses token bucket rate limiting"}
