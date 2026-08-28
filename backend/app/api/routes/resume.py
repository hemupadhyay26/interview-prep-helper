import json
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select

from app.agents import resume_agent
from app.db.database import SessionLocal
from app.db.models import Resume
from app.schemas.resume import ResumeOut
from app.services.resume_parser import parse_to_markdown, split_into_sections
from app.services.vector_store import (
    build_chunks,
    delete_resume_chunks,
    upsert_resume_chunks,
)

logger = logging.getLogger(__name__)

# The resume is global (one per app), not tied to a chat session. Upload
# it once here; every session's interview agent references it.
router = APIRouter(prefix="/resume", tags=["resume"])

MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5MB


def _to_resume_out(filename: str, profile_json: str) -> ResumeOut:
    profile = json.loads(profile_json)

    return ResumeOut(
        filename=filename,
        summary=profile["summary"],
        skills=profile["skills"],
        projects=profile["projects"],
        experience=profile["experience"],
        education=profile["education"],
    )


async def _load_resume(db) -> Resume | None:
    result = await db.execute(select(Resume).limit(1))
    return result.scalar_one_or_none()


# -------------------------------------------------------------------
# Upload / replace resume
# -------------------------------------------------------------------

@router.post("")
async def upload_resume(file: UploadFile = File(...)):
    content = await file.read()

    if len(content) > MAX_RESUME_SIZE:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Resume file too large "
                f"(max {MAX_RESUME_SIZE // (1024 * 1024)}MB)"
            ),
        )

    filename = file.filename or "resume"

    # -----------------------------------------------------------
    # Parse (Docling) + split into sections
    # -----------------------------------------------------------

    try:
        markdown = parse_to_markdown(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    sections = split_into_sections(markdown)

    # -----------------------------------------------------------
    # Structure via LLM
    # -----------------------------------------------------------

    try:
        profile_result = await resume_agent.run(markdown)
    except Exception as exc:
        logger.exception("Resume structuring failed")
        raise HTTPException(
            status_code=422,
            detail="Failed to parse resume content",
        ) from exc

    profile = profile_result.output

    # -----------------------------------------------------------
    # Persist (replaces any existing resume)
    # -----------------------------------------------------------

    async with SessionLocal() as db:
        resume = await _load_resume(db)

        if resume is None:
            resume = Resume()
            db.add(resume)

        resume.filename = filename
        resume.raw_text = markdown
        resume.profile = profile.model_dump_json()

        await db.commit()

        profile_json = resume.profile

        logger.info(
            "Resume uploaded | filename=%s | projects=%d",
            filename,
            len(profile.projects),
        )

    # -----------------------------------------------------------
    # Embed + store in the vector store
    # -----------------------------------------------------------

    chunks = build_chunks(sections, profile)
    await upsert_resume_chunks(chunks)

    return _to_resume_out(filename, profile_json)


# -------------------------------------------------------------------
# Get resume
# -------------------------------------------------------------------

@router.get("")
async def get_resume():
    async with SessionLocal() as db:
        resume = await _load_resume(db)

        if resume is None:
            raise HTTPException(
                status_code=404,
                detail="No resume uploaded",
            )

        return _to_resume_out(resume.filename, resume.profile)


# -------------------------------------------------------------------
# Delete resume
# -------------------------------------------------------------------

@router.delete("")
async def delete_resume():
    async with SessionLocal() as db:
        resume = await _load_resume(db)

        if resume is None:
            raise HTTPException(
                status_code=404,
                detail="No resume uploaded",
            )

        await db.delete(resume)
        await db.commit()

    await delete_resume_chunks()

    logger.info("Resume deleted")

    return {"success": True}
