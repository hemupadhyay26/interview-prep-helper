from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
)


def serialize_messages(messages: list[ModelMessage]) -> str:
    return ModelMessagesTypeAdapter.dump_json(messages).decode("utf-8")


def deserialize_messages(data: str) -> list[ModelMessage]:
    return ModelMessagesTypeAdapter.validate_json(data)