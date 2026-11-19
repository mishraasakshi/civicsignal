"""Repeated problems found by the AI (supervisors only).

GET /api/insights/groups - groups of similar complaints with an LLM-written summary and suggested action
"""

from pathlib import Path

from app.api.deps import require_supervisor
from app.models.user import User
from app.schemas.insights import GroupInsights
from app.services.insights import load_groups, summaries_path
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/groups", response_model=GroupInsights)
def repeated_problems(path: Path = Depends(summaries_path), _: User = Depends(require_supervisor)):
    loaded = load_groups(path)
    if loaded is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="group summaries not generated yet - run ml/models/cluster_complaints.py "
            "and ml/models/summarize_groups.py",
        )
    groups, made_at = loaded
    return GroupInsights(
        source="Pilot survey of student complaints", generated_at=made_at, groups=groups
    )
