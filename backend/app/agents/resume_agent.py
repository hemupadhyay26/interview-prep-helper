from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.agents.models import model


class ResumeProject(BaseModel):
    name: str = Field(description="The project's name or title")
    description: str = Field(
        description="What the project does/did and the candidate's role in it"
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Languages, frameworks, and tools used",
    )


class ResumeProfile(BaseModel):
    summary: str = Field(
        description="A short (1-3 sentence) summary of the candidate's profile"
    )
    skills: list[str] = Field(default_factory=list)
    projects: list[ResumeProject] = Field(default_factory=list)
    experience: list[str] = Field(
        default_factory=list,
        description=(
            "One entry per role: company, title, and a short description "
            "of responsibilities/impact"
        ),
    )
    education: list[str] = Field(default_factory=list)


resume_agent = Agent(
    model,
    name="resume_parser",
    output_type=ResumeProfile,
    system_prompt="""
You extract a structured profile from resume text.

The text was produced by a document parser and may include markdown
headings, bullet points, or minor formatting artifacts - look past
formatting noise and focus on the actual content.

Guidelines:

- List each distinct project separately in `projects`, even if the
  resume lists several under one "Projects" heading. Do not merge
  unrelated projects into one entry.
- For each project, write a description that would let someone ask a
  specific, informed follow-up question about it later - what it does,
  what the candidate built or owned, and any notable technical detail.
- `skills` should be individual skills/technologies, not sentences.
- `experience` should have one entry per role held.
- Leave a list empty if the resume genuinely has no content for it.
  Do not invent information that is not present in the text.
""",
)
