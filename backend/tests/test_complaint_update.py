"""Tests for PATCH /api/complaints/{id} (supervisor corrections + status workflow)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.classify import classifier_dependency
from app.db.session import Base, get_db
from app.main import app
from app.ml.classifier import Prediction
from app.models import complaint  # noqa: F401
from app.services.workflow import can_move


class LowConfidenceClassifier:
    model_name = "fake"

    def predict(self, text: str) -> Prediction:
        return Prediction("cleanliness", 0.3, [("cleanliness", 0.3)], True)


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
    app.dependency_overrides[classifier_dependency] = lambda: LowConfidenceClassifier()
    c = TestClient(app)
    c.post("/api/complaints", json={"text": "washroom me paani nahi aa raha"})  # id 1
    yield c
    app.dependency_overrides.clear()


def test_supervisor_corrects_category(client):
    r = client.patch("/api/complaints/1", json={"category": "water_plumbing"})
    assert r.status_code == 200
    c = r.json()
    assert c["category"] == "water_plumbing"
    assert c["predicted_category"] == "cleanliness"  # AI's original guess is kept
    assert c["needs_review"] is False


def test_normal_workflow(client):
    for s in ["Assigned", "In Progress", "Resolved", "Closed"]:
        r = client.patch("/api/complaints/1", json={"status": s})
        assert r.status_code == 200, r.json()
        assert r.json()["status"] == s


def test_cannot_skip_steps(client):
    r = client.patch("/api/complaints/1", json={"status": "Resolved"})
    assert r.status_code == 409
    assert "Allowed:" in r.json()["error"]["message"]
    assert client.get("/api/complaints/1").json()["status"] == "Submitted"  # unchanged


def test_closed_is_final(client):
    client.patch("/api/complaints/1", json={"status": "Closed"})
    r = client.patch("/api/complaints/1", json={"status": "In Progress"})
    assert r.status_code == 409
    assert "none (final)" in r.json()["error"]["message"]


def test_empty_update_and_unknown_id(client):
    assert client.patch("/api/complaints/1", json={}).status_code == 422
    assert client.patch("/api/complaints/999", json={"status": "Assigned"}).status_code == 404


def test_workflow_rules():
    assert can_move("Resolved", "In Progress")  # reopen
    assert can_move("Assigned", "Assigned")  # no change is fine
    assert not can_move("Submitted", "In Progress")
