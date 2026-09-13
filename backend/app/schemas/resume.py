"""
Structured resume model.

This is the single source of truth for the shape of a parsed resume:
`resume_agent` emits it, the `resumes` table stores it as JSON, and
`ResumeOut` (below) is just this plus the filename for the API response.
"""

from pydantic import BaseModel, Field


class ResumeContact(BaseModel):
    email: str = Field(default="", description="Primary email address, if shown")
    phone: str = Field(default="", description="Phone number, if shown")
    location: str = Field(
        default="",
        description="City / region the candidate is based in, if shown",
    )
    links: list[str] = Field(
        default_factory=list,
        description=(
            "Personal URLs from the header - portfolio, LinkedIn, GitHub, "
            "blog, etc. Always include the full https:// scheme, adding it "
            "if the resume wrote a bare domain. Do not put an email or "
            "phone number here."
        ),
    )


class ResumeExperience(BaseModel):
    company: str = Field(default="", description="Employer / organization name")
    title: str = Field(default="", description="The candidate's job title there")
    location: str = Field(default="", description="Role location, if shown")
    start_date: str = Field(
        default="",
        description="Start date exactly as written, e.g. 'Jan 2022'",
    )
    end_date: str = Field(
        default="",
        description="End date as written, or 'Present' if it is the current role",
    )
    highlights: list[str] = Field(
        default_factory=list,
        description=(
            "One entry per bullet point under this role - responsibilities, "
            "achievements, and any numbers/metrics, kept verbatim in meaning."
        ),
    )


class ResumeEducation(BaseModel):
    institution: str = Field(default="", description="School / university name")
    degree: str = Field(
        default="",
        description="Degree and field, e.g. 'B.Tech, Computer Science'",
    )
    location: str = Field(default="", description="Institution location, if shown")
    start_date: str = Field(default="", description="Start date as written")
    end_date: str = Field(
        default="",
        description="End / graduation date as written, or 'Present'",
    )
    details: list[str] = Field(
        default_factory=list,
        description="GPA, honors, relevant coursework, activities - if shown",
    )


class ResumeProject(BaseModel):
    name: str = Field(default="", description="The project's name or title")
    description: str = Field(
        default="",
        description="What it does and what the candidate built or owned",
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Languages, frameworks, and tools used",
    )
    link: str = Field(
        default="",
        description="Repo or live URL for the project, if given (full https://)",
    )


class ResumeProfile(BaseModel):
    name: str = Field(
        default="",
        description=(
            "The candidate's full name - almost always the most prominent "
            "line at the top of the resume. Empty only if genuinely absent."
        ),
    )
    headline: str = Field(
        default="",
        description=(
            "The role/tagline shown under the name, e.g. 'DevOps Engineer'. "
            "Empty if there isn't one."
        ),
    )
    contact: ResumeContact = Field(default_factory=ResumeContact)
    summary: str = Field(
        default="",
        description="The summary / objective / about section, if present",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Individual skills / technologies, not sentences",
    )
    experience: list[ResumeExperience] = Field(
        default_factory=list,
        description="One entry per role held, most recent first",
    )
    projects: list[ResumeProject] = Field(
        default_factory=list,
        description=(
            "One entry per distinct project, even if several sit under one "
            "'Projects' heading. Never merge unrelated projects."
        ),
    )
    education: list[ResumeEducation] = Field(
        default_factory=list,
        description="One entry per degree / school",
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Certifications and licenses, one per entry",
    )
    awards: list[str] = Field(
        default_factory=list,
        description="Awards, honors, and recognitions, one per entry",
    )
    languages: list[str] = Field(
        default_factory=list,
        description="Spoken/written human languages, e.g. 'English (fluent)'",
    )

    @classmethod
    def from_stored(cls, data: dict) -> "ResumeProfile":
        """
        Build a profile from a stored JSON dict, upgrading the older flat
        shape (top-level ``location``/``links``; ``experience`` and
        ``education`` as ``list[str]``) so pre-existing rows still load
        instead of failing validation.
        """
        data = dict(data or {})

        contact = dict(data.get("contact") or {})
        for key in ("email", "phone", "location", "links"):
            value = data.pop(key, None)
            if value not in (None, "", []) and not contact.get(key):
                contact[key] = value
        if contact:
            data["contact"] = contact

        exp = data.get("experience")
        if isinstance(exp, list):
            data["experience"] = [
                {"highlights": [item]} if isinstance(item, str) else item
                for item in exp
            ]

        edu = data.get("education")
        if isinstance(edu, list):
            data["education"] = [
                {"institution": item} if isinstance(item, str) else item
                for item in edu
            ]

        return cls.model_validate(data)


class ResumeOut(ResumeProfile):
    """`GET`/`POST /resume` response - the profile plus its source filename."""

    filename: str
