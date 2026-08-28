from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.core.config import settings


model = OpenAIResponsesModel(
    settings.llm_model_name,
    provider=OpenAIProvider(
        api_key=settings.openai_api_key,
    ),
)