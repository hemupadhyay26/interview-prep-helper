from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.core.config import settings

_provider = OpenAIProvider(api_key=settings.openai_api_key)


def openai_model(name: str) -> OpenAIResponsesModel:
    return OpenAIResponsesModel(name, provider=_provider)


# Main conversational / structured-extraction model.
model = openai_model(settings.llm_model_name)

# Smaller, cheaper model for lightweight side tasks (e.g. chat titles).
# Falls back to the main model when TITLE_MODEL_NAME is not set.
title_model = openai_model(settings.title_model_name or settings.llm_model_name)
