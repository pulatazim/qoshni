"""FastAPI ilovasi: modullar routerlari shu yerda ulanadi."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.db import engine
from app.core.errors import install_error_handlers
from app.modules.auth.router import router as auth_router
from app.modules.listings.router import router as listings_router
from app.modules.users.router import router as users_router

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

API_VERSION = "0.1.0"
API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=API_VERSION,
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
)


install_error_handlers(app)

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(listings_router, prefix=API_PREFIX)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": API_VERSION, "environment": settings.environment}
