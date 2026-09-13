import json
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, File, HTTPException, UploadFile
from sqlalchemy import select

from app.agents import resume_agent
from app.db.database import SessionLocal
from app.db.models import Resume
from app.schemas.resume import ResumeOut, ResumeProfile
from app.services.resume_parser import (
    extract_hyperlinks,
    extract_text,
    load_pdf_documents,
    split_documents,
)
from app.services.vector_store import (
    delete_resume_chunks,
    upsert_resume_chunks,
)

logger = logging.getLogger(__name__)

# The resume is global (one per app), not tied to a chat session. Upload
# it once here; every session's interview agent references it.
router = APIRouter(prefix="/resume", tags=["resume"])

MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5MB


def _normalize_link(link: str) -> str:
    """Resume links frequently lack a scheme (e.g. `foo.github.io`), which
    makes them resolve as relative URLs in the browser - force https."""
    link = link.strip()
    if not link or "://" in link or link.startswith(("mailto:", "tel:")):
        return link
    return f"https://{link.lstrip('/')}"


def _link_host(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def _merge_links(pdf_links: list[str], text_links: list[str]) -> list[str]:
    """
    Combine hyperlink targets pulled from the PDF's link annotations with
    the model's text-only link guesses.

    The PDF annotations carry the real destination (e.g. the full
    `linkedin.com/in/<handle>` URL) while the visible text is often just
    `linkedin.com`. When both resolve to the same host, keep the more
    specific one; drop bare email/phone links.
    """
    best: dict[str, str] = {}

    for link in (*pdf_links, *text_links):
        norm = _normalize_link(link)
        if not norm or norm.startswith(("mailto:", "tel:")):
            continue

        host = _link_host(norm)
        if not host or "." not in host:
            continue

        current = best.get(host)
        if current is None or len(norm) > len(current):
            best[host] = norm

    return list(best.values())


def _mailto_from_links(links: list[str]) -> str:
    for link in links:
        if link.lower().startswith("mailto:"):
            return link[len("mailto:"):].strip()
    return ""


def _to_resume_out(filename: str, profile_json: str) -> ResumeOut:
    profile = ResumeProfile.from_stored(json.loads(profile_json))

    # Safety net for links stored before scheme-normalization landed.
    profile.contact.links = [
        _normalize_link(link)
        for link in profile.contact.links
        if _normalize_link(link)
    ]

    return ResumeOut(filename=filename, **profile.model_dump())


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
    # Load the PDF (LangChain PyPDFLoader)
    # -----------------------------------------------------------

    try:
        documents = load_pdf_documents(filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    raw_text = extract_text(documents)

    # -----------------------------------------------------------
    # Structure via LLM
    # -----------------------------------------------------------

    try:
        profile_result = await resume_agent.run(raw_text)
    except Exception as exc:
        logger.exception("Resume structuring failed")
        raise HTTPException(
            status_code=422,
            detail="Failed to parse resume content",
        ) from exc

    profile = profile_result.output

    # Recover the real hyperlink destinations from the PDF (the text layer
    # only has the visible label, e.g. "linkedin.com").
    hyperlinks = extract_hyperlinks(content)
    profile.contact.links = _merge_links(hyperlinks, profile.contact.links)

    if not profile.contact.email:
        profile.contact.email = _mailto_from_links(hyperlinks)

    # -----------------------------------------------------------
    # Persist (replaces any existing resume)
    # -----------------------------------------------------------

    async with SessionLocal() as db:
        resume = await _load_resume(db)

        if resume is None:
            resume = Resume()
            db.add(resume)

        resume.filename = filename
        resume.raw_text = raw_text
        resume.profile = profile.model_dump_json()

        await db.commit()

        profile_json = resume.profile

        logger.info(
            "Resume uploaded | filename=%s | projects=%d",
            filename,
            len(profile.projects),
        )

    # -----------------------------------------------------------
    # Split + embed + store in the vector store
    # -----------------------------------------------------------

    chunks = split_documents(documents)
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

        if resume is not None:
            await db.delete(resume)
            await db.commit()

    # Always clear the vector store, even when the row was already gone -
    # this also sweeps up any orphaned chunks so a later `search_resume`
    # can never answer from a deleted resume.
    await delete_resume_chunks()

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="No resume uploaded",
        )

    logger.info("Resume deleted")

    return {"success": True}
