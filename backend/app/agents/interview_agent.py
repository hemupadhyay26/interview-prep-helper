import json
import logging

from pydantic_ai import Agent, RunContext
from sqlalchemy import select

from app.agents.job_agent import job_agent
from app.agents.models import model
from app.agents.question_generator import question_agent
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import JobPosting, Resume
from app.services.job_scraper import JobScrapeError, scrape_job_posting
from app.services.vector_store import search_resume_chunks

logger = logging.getLogger(__name__)


interview_agent = Agent(
    model,
    name=settings.app_name,
    deps_type=str,  # session_id, used to scope resume lookups
    system_prompt=f"""
You are {settings.app_name}, an AI interview-preparation assistant.

You are the main conversational assistant.

Have a natural conversation with the user.

Your responsibilities include:

- Understand the user's interview goal.
- Collect useful job information.
- Remember information from the conversation.
- Identify missing information.
- Ask clarification questions when necessary.
- Help the user practice interviews.
- Use specialized tools when appropriate.

If the candidate has an uploaded resume (see below), prefer grounded
questions about the specific projects, roles, and skills it mentions
over generic questions. Use the resume search tool to pull the full
detail on a project or role before asking a deep question about it.

If the user's message contains a URL to a job posting or application
page, call the `fetch_job_posting` tool with that URL to pull in the
role's details. Do this instead of asking the user to type the job
description out. If the fetch fails, ask the user to paste the job
description text and continue from that.

Do not generate structured JSON yourself.

When the user is ready for interview questions,
use the question generation tool.

Do not generate questions before enough information
about the role is available unless the user explicitly
asks for generic questions.
""",
)


@interview_agent.instructions
async def resume_context(ctx: RunContext[str]) -> str:
    """
    Prime the agent with a high-level view of the candidate's resume
    (if one has been uploaded for this session), so it steers questions
    toward what the candidate actually mentioned rather than asking
    generically.
    """

    session_id = ctx.deps

    if not session_id:
        return ""

    async with SessionLocal() as db:
        result = await db.execute(
            select(Resume).where(Resume.session_id == session_id)
        )

        resume = result.scalar_one_or_none()

    if resume is None:
        return ""

    profile = json.loads(resume.profile)

    skills = ", ".join(profile["skills"]) or "none listed"
    project_names = (
        ", ".join(project["name"] for project in profile["projects"])
        or "none listed"
    )

    return f"""
The candidate has uploaded a resume.

Skills: {skills}
Projects mentioned: {project_names}

Call the `search_resume` tool with a specific project name, role, or
topic to get its full detail before asking a deep question about it.
"""


@interview_agent.instructions
async def job_context(ctx: RunContext[str]) -> str:
    """
    Prime the agent with the structured details of the job posting the
    user pointed at (if one has been fetched for this session), so it
    steers questions toward the actual role.
    """

    session_id = ctx.deps

    if not session_id:
        return ""

    async with SessionLocal() as db:
        result = await db.execute(
            select(JobPosting).where(JobPosting.session_id == session_id)
        )

        job = result.scalar_one_or_none()

    if job is None:
        return ""

    details = json.loads(job.details)

    def _list(key: str) -> str:
        return ", ".join(details.get(key) or []) or "none listed"

    header = " - ".join(
        part
        for part in (details.get("title"), details.get("company"))
        if part
    ) or "the target role"

    return f"""
The user has provided a job posting for this session: {header}

Summary: {details.get("summary") or "n/a"}
Seniority: {details.get("seniority") or "not stated"}
Location: {details.get("location") or "not stated"}
Responsibilities: {_list("responsibilities")}
Required skills: {_list("required_skills")}
Preferred skills: {_list("preferred_skills")}
Tech stack: {_list("tech_stack")}

Ground interview questions in this role. You have enough job information
to generate questions without asking the user for more.
"""


@interview_agent.tool
async def fetch_job_posting(ctx: RunContext[str], url: str) -> str:
    """
    Fetch a job posting from `url`, extract the role's structured details,
    and store them for this session so later questions are grounded in the
    role. Call this when the user pastes a link to a job posting or
    application page.

    Returns a human-readable summary of what was extracted, or an error
    message asking the user to paste the job description text instead.
    """

    session_id = ctx.deps

    if not session_id:
        return "No active session; ask the user to paste the job description."

    try:
        markdown = await scrape_job_posting(url)
    except JobScrapeError as exc:
        return (
            f"Couldn't read that page ({exc}). Ask the user to paste the "
            "job description text and continue from that."
        )

    try:
        details = (await job_agent.run(markdown)).output
    except Exception:
        logger.exception("Job posting structuring failed | url=%s", url)
        return (
            "Couldn't make sense of that page. Ask the user to paste the "
            "job description text and continue from that."
        )

    if not details.title and not details.responsibilities and (
        not details.required_skills
    ):
        return (
            "That page didn't look like a job posting. Ask the user to "
            "paste the job description text and continue from that."
        )

    async with SessionLocal() as db:
        result = await db.execute(
            select(JobPosting).where(JobPosting.session_id == session_id)
        )

        job = result.scalar_one_or_none()

        if job is None:
            job = JobPosting(session_id=session_id)
            db.add(job)

        job.source_url = url
        job.raw_text = markdown
        job.details = details.model_dump_json()

        await db.commit()

    logger.info(
        "Job posting fetched | session=%s | url=%s | title=%s",
        session_id,
        url,
        details.title,
    )

    return (
        "Fetched the job posting. Extracted details:\n"
        f"{details.model_dump_json(indent=2)}"
    )


@interview_agent.tool
async def generate_interview_questions(
    ctx: RunContext[str],
    number_of_questions: int = 5,
) -> str:
    """
    Generate interview questions using the specialized
    question-generation agent.
    """

    result = await question_agent.run(
        f"""
Generate {number_of_questions} interview questions.

Use the information available from the conversation
to make the questions relevant to the user's role.
"""
    )

    return result.output.model_dump_json()


@interview_agent.tool
async def search_resume(ctx: RunContext[str], query: str) -> str:
    """
    Look up specific details from the candidate's uploaded resume - e.g.
    a project or role they mentioned - relevant to `query`. Use this
    before asking a deep question about something specific from their
    resume.
    """

    session_id = ctx.deps

    if not session_id:
        return "No resume on file for this session."

    chunks = await search_resume_chunks(session_id, query)

    if not chunks:
        return "No resume on file for this session."

    return "\n\n---\n\n".join(chunks)
