from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    title: Mapped[str] = mapped_column(
        String(255),
        default="New Chat",
    )

    message_history: Mapped[str] = mapped_column(
        Text,
        default="[]",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # The resume is global, not per-session: one row for the whole app,
    # re-uploading replaces it. Every chat session references it.
    filename: Mapped[str] = mapped_column(String(255))

    # Docling's markdown export of the parsed file, kept for reference
    # and re-processing without asking the user to re-upload.
    raw_text: Mapped[str] = mapped_column(Text)

    # JSON-serialized ResumeProfile (see app/agents/resume_agent.py).
    profile: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # One job posting per session - fetching another replaces the row.
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        unique=True,
    )

    # The URL the user pasted.
    source_url: Mapped[str] = mapped_column(String(2048))

    # Scraper's markdown of the posting page, kept for re-processing
    # without re-fetching.
    raw_text: Mapped[str] = mapped_column(Text)

    # JSON-serialized JobDetails (see app/agents/job_agent.py).
    details: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )