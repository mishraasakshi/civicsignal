"""POST /api/similar - search stored complaint embeddings (supervisors only)."""

import numpy as np
from app.ml.similar import DUPLICATE_THRESHOLD
from app.models.complaint import Complaint


def submit(client, headers, text):
    r = client.post("/api/complaints", json={"text": text}, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


def test_requires_login(client):
    assert client.post("/api/similar", json={"text": "wifi is slow"}).status_code == 401


def test_students_cannot_search_other_students_complaints(client, auth):
    r = client.post("/api/similar", json={"text": "wifi is slow"}, headers=auth("s@x.co"))
    assert r.status_code == 403


def test_new_complaints_store_their_embedding(client, auth, db_session_factory):
    cid = submit(client, auth("s@x.co"), "wifi is slow in the library")
    with db_session_factory() as db:
        vec = np.frombuffer(db.get(Complaint, cid).embedding, dtype="float32")
    assert vec.shape == (6,)  # the fake model's size (the real one has 384)
    assert abs(float(np.linalg.norm(vec)) - 1.0) < 1e-4  # normalised


def test_best_match_comes_first_and_shows_status(client, auth):
    student = auth("s@x.co")
    submit(client, student, "want token system in mess")
    wifi_id = submit(client, student, "wifi is slow")
    submit(client, student, "geyser has no hot water")

    r = client.post(
        "/api/similar",
        json={"text": "the wifi is very slow", "min_score": 0},
        headers=auth("boss@x.co", role="supervisor"),
    )
    body = r.json()
    assert r.status_code == 200
    assert body["searched"] == 3
    assert body["matches"][0]["id"] == wifi_id
    assert body["matches"][0]["status"] == "Submitted"
    scores = [m["score"] for m in body["matches"]]
    assert scores == sorted(scores, reverse=True)


def test_exact_repeat_is_flagged_as_possible_duplicate(client, auth):
    submit(client, auth("s@x.co"), "wifi slow wifi slow")
    r = client.post(
        "/api/similar",
        json={"text": "wifi slow wifi slow"},
        headers=auth("boss@x.co", role="supervisor"),
    )
    assert r.json()["matches"][0]["score"] >= DUPLICATE_THRESHOLD
    assert r.json()["possible_duplicate"] is True


def test_min_score_hides_weak_matches_and_empty_db_is_fine(client, auth):
    sup = auth("boss@x.co", role="supervisor")
    r = client.post("/api/similar", json={"text": "wifi"}, headers=sup)
    assert r.json() == {"searched": 0, "possible_duplicate": False, "matches": []}
    submit(client, auth("s@x.co"), "geyser has no hot water")
    r = client.post("/api/similar", json={"text": "wifi", "min_score": 0.9}, headers=sup)
    assert r.json()["matches"] == []


def test_list_endpoint_never_returns_the_embedding(client, auth):
    student = auth("s@x.co")
    submit(client, student, "wifi is slow")
    item = client.get("/api/complaints", headers=student).json()["items"][0]
    assert "embedding" not in item
