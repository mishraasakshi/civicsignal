"""PATCH /api/complaints/{id}: supervisors only, category correction, status workflow."""

import pytest
from app.services.workflow import can_move


@pytest.fixture
def boss(client, auth):
    student = auth("student@x.co")
    client.post(
        "/api/complaints", json={"text": "washroom me paani nahi aa raha"}, headers=student
    )  # id 1
    return auth("boss@x.co", role="supervisor")


def test_students_cannot_update(client, auth, boss):
    student2 = auth("other@x.co")
    r = client.patch("/api/complaints/1", json={"status": "Closed"}, headers=student2)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


def test_supervisor_corrects_category(client, boss):
    c = client.patch("/api/complaints/1", json={"category": "water_plumbing"}, headers=boss).json()
    assert c["category"] == "water_plumbing"
    assert c["predicted_category"] == "cleanliness"  # AI's original guess kept
    assert c["needs_review"] is False


def test_normal_workflow(client, boss):
    for s in ["Assigned", "In Progress", "Resolved", "Closed"]:
        r = client.patch("/api/complaints/1", json={"status": s}, headers=boss)
        assert r.status_code == 200, r.json()


def test_cannot_skip_steps_and_closed_is_final(client, boss):
    r = client.patch("/api/complaints/1", json={"status": "Resolved"}, headers=boss)
    assert r.status_code == 409 and r.json()["error"]["code"] == "CONFLICT"
    client.patch("/api/complaints/1", json={"status": "Closed"}, headers=boss)
    assert (
        "none (final)"
        in client.patch("/api/complaints/1", json={"status": "In Progress"}, headers=boss).json()[
            "error"
        ]["message"]
    )


def test_empty_update_and_unknown_id(client, boss):
    assert client.patch("/api/complaints/1", json={}, headers=boss).status_code == 422
    assert (
        client.patch("/api/complaints/999", json={"status": "Assigned"}, headers=boss).status_code
        == 404
    )


def test_workflow_rules():
    assert can_move("Resolved", "In Progress")
    assert can_move("Assigned", "Assigned")
    assert not can_move("Submitted", "In Progress")
