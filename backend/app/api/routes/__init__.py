from fastapi import APIRouter

from app.api.routes import health, job, resume, sessions

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sessions.router)
api_router.include_router(resume.router)
api_router.include_router(job.router)

__all__ = ["api_router"]
