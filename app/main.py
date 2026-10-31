from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from . import config
from .database import SessionLocal, init_db
from .routers import criminals, hunts
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    if config.AUTO_SEED:
        with SessionLocal() as db:
            seed_if_empty(db)
    yield


app = FastAPI(
    title="Space Bounty Hunters API",
    version="1.0.0",
    description="Database of wanted criminals and a journal of the bounty hunters' own capture attempts.",
    lifespan=lifespan,
)

app.include_router(criminals.router, prefix="/api")
app.include_router(hunts.router, prefix="/api")


@app.get("/", tags=["System"])
def root():
    return {"name": "Space Bounty Hunters API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["System"])
def health():
    """Liveness + database connectivity check (used by Docker HEALTHCHECK)."""
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "up"}
