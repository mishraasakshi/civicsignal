"""Response shapes for /api/insights."""

from datetime import datetime
from typing import Literal

from app.schemas.complaint import Category
from pydantic import BaseModel, Field


class GroupInsight(BaseModel):
    group: int
    size: int = Field(description="how many complaints are in this group")
    title: str
    summary: str
    category: Category
    urgency: Literal["low", "medium", "high"]
    suggested_action: str
    # complaint ids and texts are deliberately NOT included


class GroupInsights(BaseModel):
    source: str = Field(description="where the complaints came from")
    generated_at: datetime
    groups: list[GroupInsight]
