"""Shared test setup: a fresh in-memory database, a fake classifier, and login helpers.

Real PostgreSQL, the real model and the network are never used.
"""

import numpy as np
import pytest
from app.api.classify import classifier_dependency
from app.core import rate_limit
from app.core.security import hash_password
from app.db.session import Base, get_db
from app.main import app
from app.ml.classifier import Prediction
from app.models import complaint, group_insight, user  # noqa: F401  (register tables)
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

WORDS = ["wifi", "slow", "mess", "token", "geyser", "water"]


class FakeClassifier:
    """Stands in for the real model: 'embeddings' are normalised counts of a few words."""

    model_name = "fake-model"

    def encode(self, texts: list[str]) -> np.ndarray:
        v = np.array([[t.lower().count(w) for w in WORDS] for t in texts], dtype="float32") + 1e-6
        return v / np.linalg.norm(v, axis=1, keepdims=True)

    def predict_vector(self, vector: np.ndarray) -> Prediction:
        if (
            vector[WORDS.index("wifi")] > 0.5
        ):  # clearly about wifi (texts with no known words score ~0.41)
            return Prediction("internet_wifi", 0.9, [("internet_wifi", 0.9)], False)
        return Prediction("cleanliness", 0.3, [("cleanliness", 0.3)], True)

    def predict(self, text: str) -> Prediction:
        return self.predict_vector(self.encode([text])[0])


@pytest.fixture
def db_session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def client(db_session_factory):
    def test_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides.clear()  # start clean, whatever other tests did
    rate_limit.clear_all()  # every test starts with fresh login/sign-up limits
    app.dependency_overrides[get_db] = test_db
    app.dependency_overrides[classifier_dependency] = lambda: FakeClassifier()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session_factory):
    def _make(email: str, role: str = "reporter", password: str = "password123") -> User:
        with db_session_factory() as db:
            u = User(email=email, hashed_password=hash_password(password), role=role)
            db.add(u)
            db.commit()
            db.refresh(u)
            return u

    return _make


@pytest.fixture
def auth(client, make_user):
    """auth("student@x.com") -> headers with a real login token for a new user."""

    def _auth(email: str, role: str = "reporter") -> dict:
        make_user(email, role)
        r = client.post("/api/auth/login", data={"username": email, "password": "password123"})
        assert r.status_code == 200, r.json()
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _auth
