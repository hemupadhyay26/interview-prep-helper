import logging

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from sqlalchemy import select

from app.agents.models import model
from app.db.database import SessionLocal
from app.db.models import JobPosting
from app.services.job_scraper import JobScrapeError, scrape_job_posting

logger = logging.getLogger(__name__)


class JobDetails(BaseModel):
    summary: str = Field(
        description="A short (1-3 sentence) summary of the role"
    )
    title: str = Field(description="The job title", default="")
    company: str = Field(
        description="The hiring company, if stated", default=""
    )
    location: str = Field(
        description="Location and/or remote policy, if stated", default=""
    )
    employment_type: str = Field(
        description="Full-time, contract, internship, etc., if stated",
        default="",
    )
    seniority: str = Field(
        description="Seniority level (junior/mid/senior/staff/...), if stated",
        default="",
    )
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Key responsibilities / what the person will do",
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="Must-have skills, technologies, and qualifications",
    )
    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Nice-to-have skills and qualifications",
    )
    tech_stack: list[str] = Field(
        default_factory=list,
        description="Languages, frameworks, and tools the role uses",
    )


job_agent = Agent(
    model,
    name="job_parser",
    output_type=JobDetails,
    system_prompt="""
You extract a structured job description from the text of a job posting
page.

The text was scraped from a web page and may include navigation labels,
cookie banners, "apply now" boilerplate, benefits marketing, and other
noise - look past it and focus on the actual role.

Guidelines:

- `required_skills` vs `preferred_skills`: split them the way the posting
  does ("requirements" / "must have" vs "nice to have" / "bonus"). If the
  posting does not distinguish, put everything in `required_skills`.
- `responsibilities` should be short, individual bullet-style entries.
- `tech_stack` is individual technologies, not sentences.
- Leave a field empty / a list empty if the posting genuinely does not
  state it. Do not invent information that is not in the text.
- If the text is clearly not a job posting (e.g. a login wall, an error
  page, or an unrelated page), return empty values.
""",
)


class JobIngestError(Exception):
    """Raised when a job URL could not be turned into a stored posting."""


async def ingest_job_posting(session_id: str, url: str) -> JobDetails:
    """
    Scrape `url`, extract structured `JobDetails`, and upsert the
    `JobPosting` row for `session_id` (one posting per session, so a
    second call replaces it).

    Shared by `POST /sessions/{id}/job` and the interview agent's
    `fetch_job_posting` tool. Raises `JobIngestError` with a
    user-facing message on any failure.
    """

    try:
        markdown = await scrape_job_posting(url)
    except JobScrapeError as exc:
        raise JobIngestError(str(exc)) from exc

    try:
        details = (await job_agent.run(markdown)).output
    except Exception as exc:
        logger.exception("Job posting structuring failed | url=%s", url)
        raise JobIngestError(
            "Could not make sense of that page."
        ) from exc

    if not (
        details.title or details.responsibilities or details.required_skills
    ):
        raise JobIngestError("That page did not look like a job posting.")

    async with SessionLocal() as db:
        job = (
            await db.execute(
                select(JobPosting).where(
                    JobPosting.session_id == session_id
                )
            )
        ).scalar_one_or_none()

        if job is None:
            job = JobPosting(session_id=session_id)
            db.add(job)

        job.source_url = url
        job.raw_text = markdown
        job.details = details.model_dump_json()

        await db.commit()

    logger.info(
        "Job posting ingested | session=%s | url=%s | title=%s",
        session_id,
        url,
        details.title,
    )

    return details
