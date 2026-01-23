from typing import Union

from fastapi import FastAPI, Request, HTTPException, status
from pydantic import BaseModel

from hodor import TokenBucket, get_ratelimiter_instance, sync_ratelimiter, async_ratelimiter 


app = FastAPI()


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


@app.get("/items/{item_id}")
@async_ratelimiter
async def read_item_1(item_id: int, request: Request, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {"item_name": item.name, "item_id": item_id}
