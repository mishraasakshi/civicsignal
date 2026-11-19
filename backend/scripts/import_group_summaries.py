"""Copy the AI's repeated-problem summaries into the database.

Run from the project root (after ml/models/summarize_groups.py and `alembic upgrade head`):
    backend/venv/bin/python backend/scripts/import_group_summaries.py
    backend/venv/bin/python backend/scripts/import_group_summaries.py --file other.json --source "Spring survey"

Replaces the stored groups. Only summaries are stored - complaint ids and texts are dropped.
"""

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

from app.db.session import SessionLocal  # noqa: E402
from app.models import complaint, group_insight, user  # noqa: E402,F401
from app.services.insights import replace_groups  # noqa: E402

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "data/processed/real_group_summaries_v1.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--source", default="Pilot survey of student complaints")
    args = parser.parse_args()

    if not args.file.exists():
        sys.exit(f"{args.file} not found - run ml/models/summarize_groups.py first")
    groups = json.loads(args.file.read_text(encoding="utf-8"))
    made_at = datetime.fromtimestamp(args.file.stat().st_mtime, tz=UTC)
    with SessionLocal() as db:
        n = replace_groups(db, groups, args.source, made_at)
    print(f"Imported {n} group(s) from {args.file.name} (source: {args.source!r}).")


if __name__ == "__main__":
    main()
