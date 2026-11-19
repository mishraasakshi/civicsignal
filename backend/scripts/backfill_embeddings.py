"""Compute embeddings for complaints that don't have one yet (e.g. created before 0004).

Run from the project root (after `alembic upgrade head`):
    backend/venv/bin/python backend/scripts/backfill_embeddings.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/

from app.db.session import SessionLocal  # noqa: E402
from app.ml.classifier import get_classifier  # noqa: E402
from app.ml.similar import to_bytes  # noqa: E402
from app.models import complaint, user  # noqa: E402,F401
from app.models.complaint import Complaint  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main() -> None:
    with SessionLocal() as db:
        todo = db.scalars(select(Complaint).where(Complaint.embedding.is_(None))).all()
        if not todo:
            print("All complaints already have embeddings.")
            return
        print(f"Embedding {len(todo)} complaint(s)...")
        vectors = get_classifier().encode([c.text for c in todo])
        for c, v in zip(todo, vectors, strict=True):
            c.embedding = to_bytes(v)
        db.commit()
        print(f"Done: {len(todo)} complaint(s) updated.")


if __name__ == "__main__":
    main()
