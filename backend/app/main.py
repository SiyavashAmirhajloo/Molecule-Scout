from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from sqlalchemy import text

from app.api import jobs
from app.config import settings
from app.db import engine, ensure_pgvector


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        await ensure_pgvector()
    except Exception:
        pass
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Molecule Scout", lifespan=lifespan)
    app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

    @app.get("/health")
    async def health() -> dict:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db = "ok"
        except Exception:
            db = "error"
        try:
            client = redis.from_url(settings.redis_url)
            await client.ping()
            await client.aclose()
            cache = "ok"
        except Exception:
            cache = "error"
        return {"db": db, "redis": cache}

    return app


app = create_app()
