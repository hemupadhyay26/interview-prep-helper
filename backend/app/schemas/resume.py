from pydantic import BaseModel


class ResumeProjectOut(BaseModel):
    name: str
    description: str
    technologies: list[str]


class ResumeOut(BaseModel):
    session_id: str
    filename: str
    summary: str
    skills: list[str]
    projects: list[ResumeProjectOut]
    experience: list[str]
    education: list[str]
