from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.database import dispose_database_engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    dispose_database_engine()


app = FastAPI(title="Financial Plan API", lifespan=lifespan)
app.include_router(health_router)
