"""/api/complaints: submit, list, get - with login and privacy rules."""


def test_must_be_logged_in(client):
    assert client.post("/api/complaints", json={"text": "wifi down"}).status_code == 401
    assert client.get("/api/complaints").status_code == 401


def test_create_classifies_and_saves(client, auth):
    me = auth("s1@x.co")
    r = client.post(
        "/api/complaints",
        json={"text": "  wifi   not working ", "location": "Hostel B", "urgency": "high"},
        headers=me,
    )
    assert r.status_code == 201
    c = r.json()
    assert c["text"] == "wifi not working"
    assert c["category"] == c["predicted_category"] == "internet_wifi"
    assert c["status"] == "Submitted"
    assert "reporter_id" not in c  # identity never returned


def test_students_see_only_their_own(client, auth):
    alice, bob = auth("alice@x.co"), auth("bob@x.co")
    client.post("/api/complaints", json={"text": "wifi slow"}, headers=alice)
    client.post("/api/complaints", json={"text": "dirty corridor"}, headers=bob)

    a = client.get("/api/complaints", headers=alice).json()
    assert a["total"] == 1 and a["items"][0]["text"] == "wifi slow"
    assert (
        client.get("/api/complaints/2", headers=alice).status_code == 404
    )  # bob's: looks like it does not exist


def test_supervisor_sees_all_with_filters(client, auth):
    s = auth("s@x.co")
    for t in ["wifi slow", "dirty corridor", "wifi down again"]:
        client.post("/api/complaints", json={"text": t}, headers=s)
    boss = auth("boss@x.co", role="supervisor")

    everything = client.get("/api/complaints", headers=boss).json()
    assert everything["total"] == 3
    assert everything["items"][0]["text"] == "wifi down again"  # newest first
    assert (
        client.get("/api/complaints", params={"category": "internet_wifi"}, headers=boss).json()[
            "total"
        ]
        == 2
    )
    review = client.get("/api/complaints", params={"needs_review": True}, headers=boss).json()
    assert [c["text"] for c in review["items"]] == ["dirty corridor"]
    page = client.get("/api/complaints", params={"limit": 1, "offset": 1}, headers=boss).json()
    assert page["total"] == 3 and len(page["items"]) == 1
    assert client.get("/api/complaints/999", headers=boss).status_code == 404


def test_bad_input_is_rejected(client, auth):
    me = auth("s@x.co")
    assert (
        client.post(
            "/api/complaints", json={"text": "wifi", "urgency": "extreme"}, headers=me
        ).status_code
        == 422
    )
    assert (
        client.get("/api/complaints", params={"category": "plumbing"}, headers=me).status_code
        == 422
    )
    assert client.get("/api/complaints", params={"status": "Done"}, headers=me).status_code == 422
