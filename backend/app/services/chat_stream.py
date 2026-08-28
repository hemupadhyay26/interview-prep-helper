import json
import logging
from collections.abc import AsyncIterator

from pydantic_ai.messages import ModelMessage
from sqlalchemy import select

from app.agents import interview_agent, title_agent
from app.db.database import SessionLocal
from app.db.models import ChatSession
from app.services.memory import serialize_messages

logger = logging.getLogger(__name__)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def stream_chat_response(
    session_id: str,
    message: str,
    message_history: list[ModelMessage],
) -> AsyncIterator[str]:
    """
    Run the interview agent for `message`, yielding Server-Sent Events as
    the response streams in, then persist the updated conversation + title.

    Events:
    - "chunk": {"text": str}                        one per text delta
    - "done":  {"session_id": str, "title": str}     once, on success
    - "error": {"detail": str}                       once, in place of "done"
    """

    # -----------------------------------------------------------
    # Stream the response
    # -----------------------------------------------------------

    try:
        async with interview_agent.run_stream(
            message,
            message_history=message_history,
            deps=session_id,
        ) as agent_result:
            async for delta in agent_result.stream_text(delta=True):
                yield _sse("chunk", {"text": delta})

            updated_history = agent_result.all_messages()
    except Exception:
        logger.exception(
            "Chat streaming failed | session=%s",
            session_id,
        )
        yield _sse("error", {"detail": "Failed to generate a response"})
        return

    # -----------------------------------------------------------
    # Persist conversation memory + title
    # -----------------------------------------------------------

    title_result = await title_agent.run(message)
    title_data = title_result.output

    async with SessionLocal() as db:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id
            )
        )

        session = result.scalar_one_or_none()

        if session is None:
            # Session was deleted while the response was streaming.
            logger.warning(
                "Session disappeared mid-stream | session=%s",
                session_id,
            )
            yield _sse("error", {"detail": "Chat session no longer exists"})
            return

        session.message_history = serialize_messages(updated_history)

        if title_data.should_update:
            session.title = title_data.title

            logger.info(
                "Session title updated | session=%s | title=%s",
                session_id,
                session.title,
            )

        await db.commit()

        logger.info(
            "Chat response generated | session=%s",
            session_id,
        )

        yield _sse("done", {"session_id": session.id, "title": session.title})
