"""Tests for POST /api/classify. A fake classifier is used, so tests are fast and need no model files."""

from app.api.classify import classifier_dependency
from app.main import app
from app.ml.classifier import Prediction
from fastapi.testclient import TestClient


class FakeClassifier:
    model_name = "fake-model"

    def predict(self, text: str) -> Prediction:
        if "geyser" in text.lower():
            return Prediction(
                "electrical",
                0.91,
                [("electrical", 0.91), ("water_plumbing", 0.06), ("other", 0.01)],
                False,
            )
        return Prediction(
            "other", 0.30, [("other", 0.30), ("mess_food", 0.25), ("cleanliness", 0.2)], True
        )


def make_client() -> TestClient:
    app.dependency_overrides[classifier_dependency] = lambda: FakeClassifier()
    return TestClient(app)


def test_classify_returns_category_and_top3():
    r = make_client().post("/api/classify", json={"text": "Hostel B geyser kharab hai"})
    assert r.status_code == 200
    data = r.json()
    assert data["category"] == "electrical"
    assert data["needs_review"] is False
    assert len(data["top3"]) == 3
    assert data["top3"][0] == {"category": "electrical", "probability": 0.91}


def test_low_confidence_is_flagged_for_review():
    r = make_client().post("/api/classify", json={"text": "something odd happened"})
    assert r.status_code == 200
    assert r.json()["needs_review"] is True


def test_blank_text_is_rejected():
    r = make_client().post("/api/classify", json={"text": "   "})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_text_is_rejected():
    r = make_client().post("/api/classify", json={})
    assert r.status_code == 422
