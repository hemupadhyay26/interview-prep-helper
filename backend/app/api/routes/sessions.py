import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.db.database import SessionLocal
from app.db.models import ChatSession
from app.schemas.chat import ChatRequest
from app.schemas.session import SessionUpdate
from app.services.chat_stream import stream_chat_response
from app.services.memory import deserialize_messages

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


# -------------------------------------------------------------------
# Create chat session
# -------------------------------------------------------------------

@router.post("")
async def create_session():
    async with SessionLocal() as db:
        session = ChatSession(
            id=str(uuid4()),
            title="New Chat",
        )

        db.add(session)

        await db.commit()
        await db.refresh(session)

        logger.info(
            "Created chat session: %s",
            session.id,
        )

        return {
            "session_id": session.id,
            "title": session.title,
        }


# -------------------------------------------------------------------
# Get session
# -------------------------------------------------------------------

@router.get("/{session_id}")
async def get_session(session_id: str):

    async with SessionLocal() as db:

        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id
            )
        )

        session = result.scalar_one_or_none()

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found",
            )

        return {
            "session_id": session.id,
            "title": session.title,
            "message_history": session.message_history,
        }


# -------------------------------------------------------------------
# Update session
# -------------------------------------------------------------------

@router.patch("/{session_id}")
async def update_session(
    session_id: str,
    request: SessionUpdate,
):
    async with SessionLocal() as db:

        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id
            )
        )

        session = result.scalar_one_or_none()

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found",
            )

        session.title = request.title

        await db.commit()
        await db.refresh(session)

        logger.info(
            "Session renamed | session=%s | title=%s",
            session_id,
            session.title,
        )

        return {
            "session_id": session.id,
            "title": session.title,
        }


# -------------------------------------------------------------------
# Chat (streamed as Server-Sent Events)
# -------------------------------------------------------------------

@router.post("/{session_id}/chat")
async def chat(
    session_id: str,
    request: ChatRequest,
):
    logger.info(
        "Chat request received | session=%s",
        session_id,
    )

    async with SessionLocal() as db:

        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id
            )
        )

        session = result.scalar_one_or_none()

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found",
            )

        message_history = deserialize_messages(
            session.message_history
        )

    return StreamingResponse(
        stream_chat_response(
            session_id,
            request.message,
            message_history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# -------------------------------------------------------------------
# List sessions
# -------------------------------------------------------------------

@router.get("")
async def list_sessions():
    async with SessionLocal() as db:

        result = await db.execute(
            select(ChatSession)
        )

        sessions = result.scalars().all()

        return [
            {
                "session_id": session.id,
                "title": session.title,
            }
            for session in sessions
        ]


# -------------------------------------------------------------------
# Delete session
# -------------------------------------------------------------------

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    async with SessionLocal() as db:

        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id
            )
        )

        session = result.scalar_one_or_none()

        if session is None:
            raise HTTPException(
                status_code=404,
                detail="Chat session not found",
            )

        await db.delete(session)
        await db.commit()

        logger.info(
            "Deleted chat session: %s",
            session_id,
        )

        return {
            "success": True,
            "session_id": session_id,
        }
