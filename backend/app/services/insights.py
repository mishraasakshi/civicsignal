"""Read the repeated-problem groups made offline by the ML scripts.

The groups come from:
    ml/models/cluster_complaints.py   (MiniLM embeddings + DBSCAN -> groups)
    ml/models/summarize_groups.py     (Groq LLM -> title, summary, urgency, action)
They are saved to data/processed/real_group_summaries_v1.json (git-ignored).
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from app.ml.classifier import PROJECT_ROOT

SUMMARIES_PATH = PROJECT_ROOT / "data" / "processed" / "real_group_summaries_v1.json"
URGENCY_ORDER = {"high": 0, "medium": 1, "low": 2}


def summaries_path() -> Path:
    """FastAPI dependency (tests swap in a temporary file)."""
    return SUMMARIES_PATH


def load_groups(path: Path) -> tuple[list[dict], datetime] | None:
    """Return (groups, when the file was made), most urgent and biggest first. None if not generated yet."""
    if not path.exists():
        return None
    groups = json.loads(path.read_text(encoding="utf-8"))
    groups.sort(key=lambda g: (URGENCY_ORDER.get(g.get("urgency"), 9), -int(g.get("size", 0))))
    made_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return groups, made_at
