import json
import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.agents.job_agent import JobIngestError, ingest_job_posting
from app.db.database import SessionLocal
from app.db.models import ChatSession, JobPosting
from app.schemas.job import JobIn, JobOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["job"])

_DEFAULT_TITLES = {"", "New Chat"}


def _job_title(details) -> str:
    label = " · ".join(p for p in (details.title, details.company) if p)
    return (label or "Job posting")[:255]


def _to_job_out(session_id: str, source_url: str, details_json: str) -> JobOut:
    details = json.loads(details_json)

    return JobOut(
        session_id=session_id,
        source_url=source_url,
        summary=details.get("summary", ""),
        title=details.get("title", ""),
        company=details.get("company", ""),
        location=details.get("location", ""),
        employment_type=details.get("employment_type", ""),
        seniority=details.get("seniority", ""),
        responsibilities=details.get("responsibilities", []),
        required_skills=details.get("required_skills", []),
        preferred_skills=details.get("preferred_skills", []),
        tech_stack=details.get("tech_stack", []),
    )


# -------------------------------------------------------------------
# Add / replace job posting from a URL
# -------------------------------------------------------------------

@router.post("/{session_id}/job")
async def add_job(session_id: str, payload: JobIn):
    url = str(payload.url)

    async with SessionLocal() as db:
        session = (
            await db.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
        ).scalar_one_or_none()

        if session is None:
            raise HTTPException(status_code=404, detail="Chat session not found")

    # Scrape + structure + persist the JobPosting row for this session.
    try:
        details = await ingest_job_posting(session_id, url)
    except JobIngestError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Name the session after the role if the user hasn't titled it yet, so
    # the sidebar reflects which job this conversation is about.
    async with SessionLocal() as db:
        session = (
            await db.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
        ).scalar_one_or_none()

        if session is not None and session.title in _DEFAULT_TITLES:
            session.title = _job_title(details)
            await db.commit()

    logger.info("Job posting added | session=%s | url=%s", session_id, url)

    return _to_job_out(session_id, url, details.model_dump_json())


# -------------------------------------------------------------------
# Get job posting
# -------------------------------------------------------------------

@router.get("/{session_id}/job")
async def get_job(session_id: str):
    async with SessionLocal() as db:
        result = await db.execute(
            select(JobPosting).where(JobPosting.session_id == session_id)
        )

        job = result.scalar_one_or_none()

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="No job posting fetched for this session",
            )

        return _to_job_out(session_id, job.source_url, job.details)


# -------------------------------------------------------------------
# Delete job posting
# -------------------------------------------------------------------

@router.delete("/{session_id}/job")
async def delete_job(session_id: str):
    async with SessionLocal() as db:
        result = await db.execute(
            select(JobPosting).where(JobPosting.session_id == session_id)
        )

        job = result.scalar_one_or_none()

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="No job posting fetched for this session",
            )

        await db.delete(job)
        await db.commit()

    logger.info("Job posting deleted | session=%s", session_id)

    return {"success": True, "session_id": session_id}
