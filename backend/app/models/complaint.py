"""The complaints table."""

from datetime import datetime

from app.db.session import Base
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, deferred, mapped_column


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(200))
    urgency_reported: Mapped[str | None] = mapped_column(String(10))  # what the student chose

    # Who submitted it. Used only so students can see their own complaints;
    # it is never shown to supervisors (students can complain without fear).
    reporter_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # What the AI suggested when the complaint arrived (kept for measuring the model later)
    predicted_category: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    needs_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # The current category (a supervisor may correct the AI) and workflow status
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Submitted", index=True)

    # The text's meaning as 384 float32 numbers (from the classifier), for "similar complaints".
    # deferred: only loaded when a query asks for it, so normal lists stay small.
    embedding: Mapped[bytes | None] = deferred(mapped_column(LargeBinary, nullable=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
