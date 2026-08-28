import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.observability import setup_observability

setup_logging()
logger = logging.getLogger(__name__)

# Observability must be set up before any agents are constructed, so that
# Agent.instrument_all() (called inside setup_observability) applies to
# every agent instance. app.api.routes imports app.agents transitively,
# so it has to be imported after this call.
langfuse = setup_observability()

from app.api.routes import api_router  # noqa: E402

app = FastAPI(
    title=settings.app_name,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


# -------------------------------------------------------------------
# Startup
# -------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    # Schema is managed by Alembic migrations (see alembic/), not created
    # here. Run `uv run alembic upgrade head` before starting the app.
    if langfuse:
        logger.info("Langfuse observability ready")
