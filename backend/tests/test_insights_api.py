"""GET /api/insights/groups - repeated problems (supervisors only)."""

from datetime import UTC, datetime

import pytest
from app.models.group_insight import GroupInsight
from app.services.insights import replace_groups

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


MADE_AT = datetime(2026, 11, 19, 4, 54, tzinfo=UTC)


@pytest.fixture
def imported(db_session_factory):
    with db_session_factory() as db:
        replace_groups(db, GROUPS, "Pilot survey", MADE_AT)


def test_needs_login(client, imported):
    assert client.get("/api/insights/groups").status_code == 401


def test_students_are_forbidden(client, auth, imported):
    r = client.get("/api/insights/groups", headers=auth("student@x.com"))
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_supervisor_gets_groups_most_urgent_first(client, auth, imported):
    r = client.get("/api/insights/groups", headers=auth("boss@x.com", role="supervisor"))
    assert r.status_code == 200
    body = r.json()
    assert [g["title"] for g in body["groups"]] == [
        "Fan fell",
        "Slow wifi",
        "Token system for mess",
    ]
    assert body["source"] == "Pilot survey"
    assert body["generated_at"].startswith("2026-11-19T04:54")


def test_no_complaint_ids_or_extra_fields_are_stored_or_returned(
    client, auth, imported, db_session_factory
):
    r = client.get("/api/insights/groups", headers=auth("boss@x.com", role="supervisor"))
    for g in r.json()["groups"]:
        assert "ids" not in g and "genuine" not in g and "cluster_main_label" not in g
    assert not hasattr(GroupInsight, "ids")  # the table has no place for complaint ids


def test_nothing_imported_gives_503(client, auth):
    r = client.get("/api/insights/groups", headers=auth("boss@x.com", role="supervisor"))
    assert r.status_code == 503
    assert "import_group_summaries" in r.json()["error"]["message"]


def test_import_replaces_the_previous_set(db_session_factory, imported):
    with db_session_factory() as db:
        n = replace_groups(db, GROUPS[:1], "Second survey", MADE_AT)
        assert n == 1
        assert db.query(GroupInsight).count() == 1


def test_import_rejects_invalid_groups(db_session_factory, imported):
    bad = [{**GROUPS[0], "urgency": "extreme"}]
    with db_session_factory() as db, pytest.raises(ValueError):
        replace_groups(db, bad, "x", MADE_AT)
    with db_session_factory() as db:
        assert db.query(GroupInsight).count() == 3  # nothing changed
