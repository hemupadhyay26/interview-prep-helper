import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


def setup_observability():
    if not settings.langfuse_enabled:
        logger.info("Langfuse tracing disabled")
        return

    from langfuse import get_client
    from pydantic_ai import Agent

    langfuse = get_client()

    if not langfuse.auth_check():
        logger.error("Langfuse authentication failed")
        return

    # Instrument ALL PydanticAI agents.
    Agent.instrument_all()

    logger.info("Langfuse tracing enabled")

    return langfuse