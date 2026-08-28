from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.core.config import settings


class ChatTitle(BaseModel):
    should_update: bool = Field(
        description=(
            "Whether the conversation contains enough meaningful information "
            "to create a useful chat title."
        )
    )

    title: str | None = Field(
        default=None,
        description=(
            "A short descriptive title for the conversation. "
            "Return null when there is not enough meaningful information."
        )
    )


title_agent = Agent(
    OpenAIResponsesModel(
        settings.llm_model_name,
        provider=OpenAIProvider(
            api_key=settings.openai_api_key,
        ),
    ),
    name="chat_title_generator",
    output_type=ChatTitle,
    system_prompt="""
You generate useful titles for chat conversations.

Your job is NOT to create a title for every conversation.

First determine whether the conversation contains enough meaningful
information to create a useful and specific title.

## Do NOT create a title for filler conversations

Examples:

- "Hi"
- "Hello"
- "Hey"
- "Hey there"
- "How are you?"
- "What's up?"
- "Good morning"
- "Thanks"
- "Thank you"
- "Okay"
- "Cool"
- "Nice"
- "Can you help me?"
- Other greetings, small talk, acknowledgements, or meaningless
  starter messages

For these cases:

should_update = false
title = null

## Create a title when meaningful context exists

Examples:

- "I'm preparing for a Senior DevOps Engineer interview."
  → "Senior DevOps Interview"

- "I have an AWS Solutions Architect interview next week."
  → "AWS Solutions Architect Interview"

- "Help me prepare for a Python backend developer role using FastAPI."
  → "Python FastAPI Interview Prep"

- "I need help preparing Kubernetes questions for my DevOps interview."
  → "Kubernetes DevOps Interview"

## Title rules

When creating a title:

- Maximum 6 words.
- Make it specific and meaningful.
- Capture the main topic.
- Prefer the job, technology, project, or purpose.
- Do not include quotes.
- Do not add punctuation at the end.
- Never use generic titles such as:
  - "New Chat"
  - "Conversation"
  - "Chat"
  - "General Discussion"

Only set should_update=true when the title would actually help the user
identify this conversation later.
""",
)