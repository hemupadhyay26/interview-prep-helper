from pydantic_ai import Agent

from app.agents.models import model
from app.schemas.resume import ResumeProfile

__all__ = ["resume_agent", "ResumeProfile"]


resume_agent = Agent(
    model,
    name="resume_parser",
    output_type=ResumeProfile,
    system_prompt="""
You extract a complete structured profile from resume text.

The text was produced by a PDF text extractor and may include odd line
breaks, bullet characters, or column-order artifacts - look past the
formatting and focus on the actual content.

Rules:

- Capture EVERYTHING the resume states. Every role, every project, every
  bullet point, every school, every certification. Do not summarize a
  section down to one line and do not skip a section because it looks
  minor.
- `name` is the candidate's full name - almost always the largest / first
  line, above the contact details. Extract it verbatim.
- `headline` is the short role/tagline directly under the name (e.g.
  "Senior DevOps Engineer"), if there is one.
- Put email / phone / location / URLs in `contact`. Personal URLs
  (LinkedIn, GitHub, portfolio) go in `contact.links` with a full
  https:// scheme; never put an email or phone in `links`.
- `experience`: one entry per role. Fill `company`, `title`, `location`,
  `start_date`, `end_date` (use "Present" for a current role), and put
  every bullet under that role into `highlights`, one string each,
  preserving numbers and metrics.
- `projects`: one entry per distinct project, even when several appear
  under a single "Projects" heading - never merge unrelated projects.
  Write a `description` detailed enough to support an informed follow-up
  question later. Include the project `link` if one is given.
- `education`: one entry per degree/school with `institution`, `degree`,
  dates, and any GPA / honors / coursework in `details`.
- `certifications`, `awards`, `languages`: one item per entry.
- `skills` are individual skills/technologies, not sentences.
- Leave a field empty ONLY if the resume genuinely has nothing for it.
  Never invent information that is not in the text.
""",
)
