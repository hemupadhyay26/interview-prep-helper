import json
import logging

from pydantic_ai import Agent, RunContext
from sqlalchemy import select

from app.agents.job_agent import JobIngestError, ingest_job_posting
from app.agents.models import model
from app.agents.question_generator import question_agent
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import JobPosting, Resume
from app.schemas.resume import ResumeProfile
from app.services.vector_store import search_resume_chunks

logger = logging.getLogger(__name__)


interview_agent = Agent(
    model,
    name=settings.app_name,
    deps_type=str,  # session_id, used to scope the job posting to a session
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

Do not generate questions before enough information
about the role is available unless the user explicitly
asks for generic questions.

## Running the interview (default behaviour)

Practise like a real interviewer: ONE question at a time.

- When the user is ready to practise, call `generate_interview_questions`
  to get a set, but keep that set to yourself. Do NOT paste the whole
  list into the chat.
- Ask a single question, then stop and wait for the user's answer.
- After they answer, give short, specific feedback (what was strong, what
  was missing or wrong, one concrete tip), then ask the next question.
- Track where you are (e.g. "Question 3 of 8"). If you run out, offer to
  generate more or wrap up with an overall summary.
- If the user asks to skip, move on, go back, or change topic, follow
  that.
- Only dump the full numbered list if the user explicitly asks to just
  see all the questions (e.g. "list them", "give me all of them",
  "I don't want a mock interview") - then use the list format below.

## Formatting your replies

Reply in GitHub-flavored Markdown.

- One question at a time: put the topic in bold, then the question, on
  its own - not as a list item, e.g.
  `**AWS architecture** - Design a highly available ...`.
- Only when the user explicitly asked for the whole set: output it as a
  single Markdown ordered list (`1.`, `2.`, `3.` ...), one question per
  item, a blank line between items, topic in bold at the start of each.
  Never hand-write the numbers - let the list markers do it.
- Use `**bold**` for short emphasis, `` `code` `` for commands, config
  keys, and identifiers, and fenced code blocks for multi-line snippets.
- Keep normal explanation in short paragraphs; only use a list when the
  content is genuinely a list.
""",
)


@interview_agent.instructions
async def resume_context(ctx: RunContext[str]) -> str:
    """
    Prime the agent with a high-level view of the candidate's resume
    (if one has been uploaded - the resume is global, shared across every
    session), so it steers questions toward what the candidate actually
    mentioned rather than asking generically.
    """

    async with SessionLocal() as db:
        result = await db.execute(select(Resume).limit(1))

        resume = result.scalar_one_or_none()

    if resume is None:
        return ""

    profile = ResumeProfile.from_stored(json.loads(resume.profile))

    def _dash(value: str) -> str:
        return value.strip() or "—"

    name = profile.name.strip() or "not stated on the resume"
    headline = _dash(profile.headline)
    location = _dash(profile.contact.location)
    summary = profile.summary.strip() or "none provided"
    skills = ", ".join(profile.skills) or "none listed"
    links = ", ".join(profile.contact.links) or "none listed"
    certifications = ", ".join(profile.certifications) or "none listed"

    if profile.experience:
        experience_lines = "\n".join(
            f"- {_dash(role.title)} at {_dash(role.company)}"
            f" ({_dash(role.start_date)} - {_dash(role.end_date)})"
            for role in profile.experience
        )
    else:
        experience_lines = "- none listed"

    if profile.education:
        education_lines = "\n".join(
            f"- {_dash(edu.degree)}, {_dash(edu.institution)}"
            f" ({_dash(edu.end_date)})"
            for edu in profile.education
        )
    else:
        education_lines = "- none listed"

    project_names = (
        ", ".join(project.name for project in profile.projects if project.name)
        or "none listed"
    )

    return f"""
The candidate has uploaded a resume. High-level snapshot:

Name: {name}
Headline: {headline}
Location: {location}
Summary: {summary}
Links: {links}
Skills: {skills}
Certifications: {certifications}

Experience:
{experience_lines}

Education:
{education_lines}

Projects mentioned: {project_names}

Address the candidate by name when it is known. The links above (GitHub,
LinkedIn, portfolio, etc.) are already on file - use them directly and
never ask the candidate to paste a link or detail that is listed here.
Call the `search_resume` tool with a specific project name, company,
role, or topic to pull its full detail (bullet points, metrics, tech)
before asking a deep question about it.
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
        details = await ingest_job_posting(session_id, url)
    except JobIngestError as exc:
        return (
            f"Couldn't use that page ({exc}). Ask the user to paste the "
            "job description text and continue from that."
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
    Generate a bank of interview questions using the specialized
    question-generation agent.

    The returned JSON is for you to work through one question at a time in
    a mock interview - do not paste the whole list to the user unless they
    explicitly asked to just see all the questions.
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

    chunks = await search_resume_chunks(query)

    if not chunks:
        return "No resume on file."

    return "\n\n---\n\n".join(chunks)
