"""GET /api/insights/groups - repeated problems (supervisors only)."""

import json

import pytest
from app.main import app
from app.services.insights import summaries_path

GROUPS = [
    {
        "group": 1,
        "size": 4,
        "genuine": 4,
        "cluster_main_label": "mess_food",
        "ids": ["r1", "r2"],
        "title": "Token system for mess",
        "summary": "Four students want tokens.",
        "category": "mess_food",
        "urgency": "medium",
        "suggested_action": "Discuss with the mess committee.",
    },
    {
        "group": 2,
        "size": 2,
        "genuine": 0,
        "cluster_main_label": "electrical",
        "ids": ["r3"],
        "title": "Fan fell",
        "summary": "Two students report a falling fan.",
        "category": "electrical",
        "urgency": "high",
        "suggested_action": "Inspect fans.",
    },
    {
        "group": 3,
        "size": 5,
        "genuine": 1,
        "cluster_main_label": "internet_wifi",
        "ids": ["r4"],
        "title": "Slow wifi",
        "summary": "Five students report slow wifi.",
        "category": "internet_wifi",
        "urgency": "medium",
        "suggested_action": "Check the router.",
    },
]


@pytest.fixture
def summaries_file(tmp_path):
    path = tmp_path / "groups.json"
    path.write_text(json.dumps(GROUPS))
    app.dependency_overrides[summaries_path] = lambda: path
    return path


def test_needs_login(client, summaries_file):
    assert client.get("/api/insights/groups").status_code == 401


def test_students_are_forbidden(client, auth, summaries_file):
    r = client.get("/api/insights/groups", headers=auth("student@x.com"))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_supervisor_gets_groups_most_urgent_first(client, auth, summaries_file):
    r = client.get("/api/insights/groups", headers=auth("boss@x.com", role="supervisor"))
    assert r.status_code == 200
    body = r.json()
    titles = [g["title"] for g in body["groups"]]
    assert titles == [
        "Fan fell",
        "Slow wifi",
        "Token system for mess",
    ]  # high first, then bigger first
    assert body["generated_at"]


def test_no_complaint_ids_or_extra_fields_leak(client, auth, summaries_file):
    r = client.get("/api/insights/groups", headers=auth("boss@x.com", role="supervisor"))
    for g in r.json()["groups"]:
        assert "ids" not in g and "genuine" not in g and "cluster_main_label" not in g


def test_missing_file_gives_503(client, auth, tmp_path):
    app.dependency_overrides[summaries_path] = lambda: tmp_path / "nope.json"
    r = client.get("/api/insights/groups", headers=auth("boss@x.com", role="supervisor"))
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
