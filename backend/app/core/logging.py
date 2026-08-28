import logging

from uvicorn.logging import DefaultFormatter

from app.core.config import settings


def setup_logging() -> None:
    """Match uvicorn's own log style (e.g. "INFO:     message") instead of
    a separate timestamp/logger-name format, so app and server logs read as
    one consistent stream.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(DefaultFormatter(fmt="%(levelprefix)s %(message)s"))

    root = logging.getLogger()
    root.setLevel(settings.log_level)
    root.handlers = [handler]
