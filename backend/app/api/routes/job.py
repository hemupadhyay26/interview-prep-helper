import json
import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import JobPosting
from app.schemas.job import JobOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["job"])


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
