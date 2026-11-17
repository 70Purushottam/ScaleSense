import os
from contextlib import asynccontextmanager

import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pg = await asyncpg.create_pool(
        os.environ["DATABASE_URL"], min_size=2, max_size=10
    )
    app.state.r = aioredis.from_url(os.environ["REDIS_URL"])
    yield
    await app.state.pg.close()
    await app.state.r.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/item/{item_id}")
async def item(item_id: int):
    r = app.state.r
    cached = await r.get(f"item:{item_id}")
    if cached is not None:
        return {"v": cached.decode(), "src": "cache"}
    val = await app.state.pg.fetchval(
        "SELECT val FROM items WHERE id = $1", item_id % 1000
    )
    await r.set(f"item:{item_id}", val or "", ex=300)
    return {"v": val, "src": "db"}