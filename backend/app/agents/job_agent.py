from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.agents.models import model


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
