"""Find stored complaints that mean the same thing as a new text.

Each complaint's embedding (384 normalised float32 numbers) is saved in the database when
it is submitted. Searching = cosine similarity between the new text's embedding and all
stored ones (a dot product, because the vectors are normalised). For thousands of
complaints numpy does this in a few milliseconds, so no separate vector index is needed.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from app.models.complaint import Complaint
from sqlalchemy import select
from sqlalchemy.orm import Session

DUPLICATE_THRESHOLD = 0.90  # this similar = probably the same complaint sent twice
EMBEDDING_DTYPE = "float32"


@dataclass
class Match:
    id: int
    text: str
    category: str
    status: str
    score: float


def to_bytes(vector: np.ndarray) -> bytes:
    return np.asarray(vector, dtype=EMBEDDING_DTYPE).tobytes()


def search(
    db: Session,
    encode: Callable[[list[str]], np.ndarray],
    text: str,
    k: int = 5,
    min_score: float = 0.0,
) -> tuple[list[Match], int]:
    """Return (best matches, how many complaints were searched)."""
    rows = db.execute(
        select(
            Complaint.id, Complaint.text, Complaint.category, Complaint.status, Complaint.embedding
        ).where(Complaint.embedding.is_not(None))
    ).all()
    if not rows:
        return [], 0

    matrix = np.frombuffer(b"".join(r.embedding for r in rows), dtype=EMBEDDING_DTYPE).reshape(
        len(rows), -1
    )
    query = np.asarray(encode([text])[0], dtype=EMBEDDING_DTYPE)
    scores = matrix @ query  # cosine similarity with every stored complaint
    best = np.argsort(scores)[::-1][:k]
    matches = [
        Match(
            rows[i].id, rows[i].text, rows[i].category, rows[i].status, round(float(scores[i]), 4)
        )
        for i in best
        if scores[i] >= min_score
    ]
    return matches, len(rows)
