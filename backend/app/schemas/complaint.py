"""Request and response shapes for /api/complaints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal["water_plumbing", "electrical", "cleanliness", "internet_wifi",
                   "furniture", "mess_food", "security", "other"]
Status = Literal["Submitted", "Under Review", "Assigned", "In Progress",
                 "Resolved", "Closed", "Needs More Information"]
Urgency = Literal["low", "medium", "high"]


class ComplaintCreate(BaseModel):
    text: str = Field(min_length=3, max_length=2000,
                      examples=["Hostel B ke washroom me 3 din se paani nahi aa raha"])
    location: str | None = Field(default=None, max_length=200, examples=["Hostel B"])
    urgency: Urgency | None = Field(default=None, description="how urgent the student thinks it is")

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 3:
            raise ValueError("complaint text is too short")
        return v

    @field_validator("location")
    @classmethod
    def tidy_location(cls, v: str | None) -> str | None:
        v = " ".join(v.split()) if v else None
        return v or None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # build it straight from a database row

    id: int
    text: str
    location: str | None
    urgency_reported: str | None
    predicted_category: str
    confidence: float
    needs_review: bool
    category: str
    status: str
    created_at: datetime
    updated_at: datetime


class ComplaintList(BaseModel):
    total: int = Field(description="how many complaints match the filters (all pages)")
    items: list[ComplaintOut]
