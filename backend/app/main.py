from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from app.api import jobs, molecules, projects
from app.config import settings
from app.db import engine, upgrade_schema


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        await upgrade_schema()
    except Exception:
        pass
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Molecule Scout", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"]
    )
    app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
    app.include_router(molecules.router, prefix="/molecules", tags=["molecules"])
    app.include_router(projects.router, prefix="/projects", tags=["projects"])

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse("/docs")

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
