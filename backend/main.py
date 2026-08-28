"""Entrypoint shim so `uvicorn main:app` keeps working from backend/.

The actual FastAPI app now lives in app/main.py — see that module for
app construction, middleware, and startup wiring.
"""

import uvicorn

from app.core.config import settings
from app.main import app

__all__ = ["app"]


if __name__ == "__main__":
    # `uvicorn main:app --port X` can't read .env itself, so running this
    # file directly is what makes HOST/PORT in .env take effect.
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.env_mode.value == "development",
    )
