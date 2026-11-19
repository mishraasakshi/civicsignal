"""Repeated-problem groups (AI grouping + LLM summary), imported from the ML pipeline."""

from datetime import datetime

from app.db.session import Base
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column


class GroupInsight(Base):
    __tablename__ = "group_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_no: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)  # complaints in the group
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    urgency: Mapped[str] = mapped_column(String(10), nullable=False)
    suggested_action: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # where the complaints came from
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
