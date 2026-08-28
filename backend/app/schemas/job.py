from pydantic import BaseModel


class JobOut(BaseModel):
    session_id: str
    source_url: str
    summary: str
    title: str
    company: str
    location: str
    employment_type: str
    seniority: str
    responsibilities: list[str]
    required_skills: list[str]
    preferred_skills: list[str]
    tech_stack: list[str]
