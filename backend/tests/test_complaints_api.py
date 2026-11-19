"""Tests for /api/complaints using an in-memory SQLite database and a fake classifier.

Nothing touches the real PostgreSQL database or the real model.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.classify import classifier_dependency
from app.db.session import Base, get_db
from app.main import app
from app.ml.classifier import Prediction
from app.models import complaint  # noqa: F401  (registers the table)


class FakeClassifier:
    model_name = "fake-model"

    def predict(self, text: str) -> Prediction:
        if "wifi" in text.lower():
            return Prediction("internet_wifi", 0.9, [("internet_wifi", 0.9)], False)
        return Prediction("other", 0.3, [("other", 0.3)], True)


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[classifier_dependency] = lambda: FakeClassifier()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_classifies_and_saves(client):
    r = client.post("/api/complaints", json={"text": "  wifi   not working ", "location": "Hostel B", "urgency": "high"})
    assert r.status_code == 201
    c = r.json()
    assert c["id"] == 1
    assert c["text"] == "wifi not working"  # extra spaces tidied
    assert c["category"] == c["predicted_category"] == "internet_wifi"
    assert c["status"] == "Submitted"
    assert c["urgency_reported"] == "high"
    assert c["needs_review"] is False


def test_get_one_and_404(client):
    client.post("/api/complaints", json={"text": "wifi down"})
    assert client.get("/api/complaints/1").json()["text"] == "wifi down"
    r = client.get("/api/complaints/999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_list_filters_and_newest_first(client):
    client.post("/api/complaints", json={"text": "wifi slow"})
    client.post("/api/complaints", json={"text": "something strange"})
    client.post("/api/complaints", json={"text": "wifi down again"})

    everything = client.get("/api/complaints").json()
    assert everything["total"] == 3
    assert everything["items"][0]["text"] == "wifi down again"  # newest first

    wifi = client.get("/api/complaints", params={"category": "internet_wifi"}).json()
    assert wifi["total"] == 2

    review = client.get("/api/complaints", params={"needs_review": True}).json()
    assert [c["text"] for c in review["items"]] == ["something strange"]

    page = client.get("/api/complaints", params={"limit": 1, "offset": 1}).json()
    assert page["total"] == 3 and len(page["items"]) == 1


def test_bad_input_is_rejected(client):
    assert client.post("/api/complaints", json={"text": "wifi", "urgency": "extreme"}).status_code == 422
    assert client.get("/api/complaints", params={"category": "plumbing"}).status_code == 422
    assert client.get("/api/complaints", params={"status": "Done"}).status_code == 422
