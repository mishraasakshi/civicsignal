"""Request and response shapes for POST /api/classify."""

from pydantic import BaseModel, Field, field_validator


class ClassifyRequest(BaseModel):
    text: str = Field(
        min_length=3,
        max_length=2000,
        examples=["Hostel B ka geyser kharab hai, garam paani nahi aa raha"],
    )

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 3:
            raise ValueError("complaint text is too short")
        return v


class CategoryScore(BaseModel):
    category: str
    probability: float


class ClassifyResponse(BaseModel):
    category: str
    confidence: float = Field(description="0-1, how sure the model is")
    needs_review: bool = Field(description="true when confidence is low; a human should check")
    top3: list[CategoryScore]
    model: str
