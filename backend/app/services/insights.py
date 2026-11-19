"""Repeated-problem groups, stored in the database.

They are made offline by the ML pipeline:
    ml/models/cluster_complaints.py   (MiniLM embeddings + DBSCAN -> groups)
    ml/models/summarize_groups.py     (Groq LLM -> title, summary, urgency, action)
and copied into the database with backend/scripts/import_group_summaries.py.
Only the summaries are stored - never complaint ids or complaint text.
"""

from datetime import datetime

from app.models.group_insight import GroupInsight
from app.schemas.insights import GroupInsight as GroupInsightIn
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

URGENCY_ORDER = {"high": 0, "medium": 1, "low": 2}


def load_groups(db: Session) -> list[GroupInsight]:
    """All groups, most urgent and biggest first (empty list if none imported)."""
    rows = db.scalars(select(GroupInsight)).all()
    return sorted(rows, key=lambda g: (URGENCY_ORDER.get(g.urgency, 9), -g.size, g.group_no))


def replace_groups(db: Session, groups: list[dict], source: str, generated_at: datetime) -> int:
    """Swap the stored groups for a new set in one transaction. Returns how many were stored."""
    valid = [GroupInsightIn.model_validate(g) for g in groups]  # also drops extra fields like ids
    db.execute(delete(GroupInsight))
    db.add_all(
        GroupInsight(
            group_no=g.group,
            size=g.size,
            title=g.title,
            summary=g.summary,
            category=g.category,
            urgency=g.urgency,
            suggested_action=g.suggested_action,
            source=source,
            generated_at=generated_at,
        )
        for g in valid
    )
    db.commit()
    return len(valid)
