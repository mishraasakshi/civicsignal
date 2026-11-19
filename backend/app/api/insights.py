"""Repeated problems found by the AI (supervisors only).

GET /api/insights/groups - groups of similar complaints with an LLM-written summary and suggested action
"""

from app.api.deps import require_supervisor
from app.db.session import get_db
from app.models.user import User
from app.schemas.insights import GroupInsight, GroupInsights
from app.services.insights import load_groups
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("/groups", response_model=GroupInsights)
def repeated_problems(db: Session = Depends(get_db), _: User = Depends(require_supervisor)):
    rows = load_groups(db)
    if not rows:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="group summaries not imported yet - run backend/scripts/import_group_summaries.py",
        )
    return GroupInsights(
        source=rows[0].source,
        generated_at=max(r.generated_at for r in rows),
        groups=[
            GroupInsight(
                group=r.group_no,
                size=r.size,
                title=r.title,
                summary=r.summary,
                category=r.category,
                urgency=r.urgency,
                suggested_action=r.suggested_action,
            )
            for r in rows
        ],
    )
