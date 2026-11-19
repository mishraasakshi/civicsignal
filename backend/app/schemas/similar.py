"""Request and response shapes for POST /api/similar."""

from pydantic import BaseModel, Field, field_validator


class SimilarRequest(BaseModel):
    text: str = Field(
        min_length=3,
        max_length=2000,
        examples=["mess should have a token system instead of fixed monthly fee"],
    )
    k: int = Field(default=5, ge=1, le=20, description="how many matches to return")
    min_score: float = Field(default=0.5, ge=0.0, le=1.0, description="hide weaker matches")

    @field_validator("text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 3:
            raise ValueError("complaint text is too short")
        return v


class SimilarMatch(BaseModel):
    id: int
    text: str
    category: str
    status: str
    score: float = Field(description="cosine similarity, 1.0 = same meaning")


class SimilarResponse(BaseModel):
    searched: int = Field(description="how many past complaints were searched")
    possible_duplicate: bool = Field(description="true if the best match is almost identical")
    matches: list[SimilarMatch]
