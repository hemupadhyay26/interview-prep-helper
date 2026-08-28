import json
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select

from app.agents import resume_agent
from app.db.database import SessionLocal
from app.db.models import ChatSession, Resume
from app.schemas.resume import ResumeOut
from app.services.resume_parser import parse_to_markdown, split_into_sections
from app.services.vector_store import (
    build_chunks,
    delete_resume_chunks,
    upsert_resume_chunks,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["resume"])

MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5MB


def _to_resume_out(session_id: str, filename: str, profile_json: str) -> ResumeOut:
    profile = json.loads(profile_json)

    return ResumeOut(
        session_id=session_id,
        filename=filename,
        summary=profile["summary"],
        skills=profile["skills"],
        projects=profile["projects"],
        experience=profile["experience"],
        education=profile["education"],
    )


# -------------------------------------------------------------------
# Upload / replace resume
# -------------------------------------------------------------------

@router.post("/{session_id}/resume")
async def upload_resume(
    session_id: str,
    file: UploadFile = File(...),
):
    async with SessionLocal() as db:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )

        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found",
            )

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
        logger.exception(
            "Resume structuring failed | session=%s",
            session_id,
        )
        raise HTTPException(
            status_code=422,
            detail="Failed to parse resume content",
        ) from exc

    profile = profile_result.output

    # -----------------------------------------------------------
    # Persist (replaces any existing resume for this session)
    # -----------------------------------------------------------

    async with SessionLocal() as db:
        result = await db.execute(
            select(Resume).where(Resume.session_id == session_id)
        )

        resume = result.scalar_one_or_none()

        if resume is None:
            resume = Resume(session_id=session_id)
            db.add(resume)

        resume.filename = filename
        resume.raw_text = markdown
        resume.profile = profile.model_dump_json()

        await db.commit()

        profile_json = resume.profile

        logger.info(
            "Resume uploaded | session=%s | filename=%s | projects=%d",
            session_id,
            filename,
            len(profile.projects),
        )

    # -----------------------------------------------------------
    # Embed + store in the vector store
    # -----------------------------------------------------------

    chunks = build_chunks(sections, profile)
    await upsert_resume_chunks(session_id, chunks)

    return _to_resume_out(session_id, filename, profile_json)


# -------------------------------------------------------------------
# Get resume
# -------------------------------------------------------------------

@router.get("/{session_id}/resume")
async def get_resume(session_id: str):
    async with SessionLocal() as db:
        result = await db.execute(
            select(Resume).where(Resume.session_id == session_id)
        )

        resume = result.scalar_one_or_none()

        if resume is None:
            raise HTTPException(
                status_code=404,
                detail="No resume uploaded for this session",
            )

        return _to_resume_out(session_id, resume.filename, resume.profile)


# -------------------------------------------------------------------
# Delete resume
# -------------------------------------------------------------------

@router.delete("/{session_id}/resume")
async def delete_resume(session_id: str):
    async with SessionLocal() as db:
        result = await db.execute(
            select(Resume).where(Resume.session_id == session_id)
        )

        resume = result.scalar_one_or_none()

        if resume is None:
            raise HTTPException(
                status_code=404,
                detail="No resume uploaded for this session",
            )

        await db.delete(resume)
        await db.commit()

    await delete_resume_chunks(session_id)

    logger.info(
        "Resume deleted | session=%s",
        session_id,
    )

    return {"success": True, "session_id": session_id}
