"""Tests for POST /api/similar, using a tiny fake 'embedding' so no model is needed."""

import numpy as np
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.similar import index_dependency
from app.main import app
from app.ml.similar import SimilarIndex

WORDS = ["wifi", "slow", "mess", "token", "geyser", "water"]


def fake_encode(texts: list[str]) -> np.ndarray:
    """Count known words, then normalise - similar texts get similar vectors."""
    v = np.array([[t.lower().count(w) for w in WORDS] for t in texts], dtype="float32") + 1e-6
    return v / np.linalg.norm(v, axis=1, keepdims=True)


FAKE_INDEX = SimilarIndex(
    ids=["real_001", "real_002", "real_003"],
    texts=["wifi is slow", "want token system in mess", "geyser has no hot water"],
    categories=["internet_wifi", "mess_food", "electrical"],
    encode=fake_encode,
)


def client() -> TestClient:
    app.dependency_overrides[index_dependency] = lambda: FAKE_INDEX
    app.dependency_overrides[get_current_user] = lambda: object()  # pretend someone is logged in
    return TestClient(app)


def test_requires_login():
    app.dependency_overrides.clear()
    app.dependency_overrides[index_dependency] = lambda: FAKE_INDEX
    assert TestClient(app).post("/api/similar", json={"text": "wifi"}).status_code == 401
    app.dependency_overrides.clear()


def test_best_match_comes_first():
    r = client().post("/api/similar", json={"text": "mess token please", "k": 2, "min_score": 0})
    assert r.status_code == 200
    data = r.json()
    assert data["searched"] == 3
    assert data["matches"][0]["id"] == "real_002"
    assert len(data["matches"]) == 2


def test_exact_repeat_is_flagged_as_duplicate():
    r = client().post("/api/similar", json={"text": "wifi is slow"})
    assert r.json()["possible_duplicate"] is True
    assert r.json()["matches"][0]["score"] > 0.99


def test_min_score_hides_weak_matches():
    r = client().post("/api/similar", json={"text": "geyser water", "min_score": 0.95})
    assert [m["id"] for m in r.json()["matches"]] == ["real_003"]


def test_k_must_be_in_range():
    assert client().post("/api/similar", json={"text": "wifi slow", "k": 0}).status_code == 422
