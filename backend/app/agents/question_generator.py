from pydantic import BaseModel, Field
from pydantic_ai import Agent

from app.core.config import settings
from app.agents.models import model


class InterviewQuestion(BaseModel):
    question: str = Field(
        description="The interview question"
    )
    category: str = Field(
        description="Technical, Behavioral, Situational, or Role-specific"
    )


class InterviewQuestions(BaseModel):
    questions: list[InterviewQuestion]


question_agent = Agent(
    model,
    name="question_generator",
    output_type=InterviewQuestions,
    system_prompt="""
You generate interview questions.

Generate questions based on the job and candidate information
provided by the parent agent.

Default to 5 questions.

If a specific number is requested, generate exactly that number.

Questions should be specific to the role and provided information.

Mix:
- Technical
- Behavioral
- Situational
- Role-specific
- Experience-based
""",
)