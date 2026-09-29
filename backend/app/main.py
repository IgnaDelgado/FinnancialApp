from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.core.config import get_settings
from app.core.database import dispose_database_engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    yield
    dispose_database_engine()


app = FastAPI(title="Financial Plan API", lifespan=lifespan)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origin_list,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
)
app.include_router(health_router)
app.include_router(auth_router)
