"""Sign-up, login, /me, and role checks."""


def test_register_login_me(client):
    r = client.post("/api/auth/register", json={"email": " Student@Example.com ", "password": "longpassword"})
    assert r.status_code == 201
    assert r.json()["email"] == "student@example.com"  # tidied
    assert r.json()["role"] == "reporter"  # sign-up can never create a supervisor
    assert "password" not in str(r.json()).lower()

    token = client.post("/api/auth/login", data={"username": "student@example.com", "password": "longpassword"})
    assert token.status_code == 200
    headers = {"Authorization": f"Bearer {token.json()['access_token']}"}
    assert client.get("/api/auth/me", headers=headers).json()["email"] == "student@example.com"


def test_register_rejects_duplicates_and_bad_input(client):
    body = {"email": "a@b.co", "password": "longpassword"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409
    assert client.post("/api/auth/register", json={"email": "not-an-email", "password": "longpassword"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "c@d.co", "password": "short"}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "c@d.co", "password": "x" * 80}).status_code == 422


def test_role_cannot_be_chosen_at_signup(client):
    r = client.post("/api/auth/register", json={"email": "sneaky@x.co", "password": "longpassword", "role": "supervisor"})
    assert r.status_code == 201
    assert r.json()["role"] == "reporter"


def test_wrong_password_and_unknown_email_look_the_same(client, make_user):
    make_user("real@x.co")
    wrong_pw = client.post("/api/auth/login", data={"username": "real@x.co", "password": "nope-nope"})
    no_user = client.post("/api/auth/login", data={"username": "ghost@x.co", "password": "nope-nope"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()


def test_bad_or_missing_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_login_sets_httponly_session_cookie(client, make_user):
    make_user("cookie@x.co")
    r = client.post("/api/auth/login", data={"username": "cookie@x.co", "password": "password123"})
    assert r.status_code == 200
    set_cookie = r.headers["set-cookie"].lower()
    assert "cs_session=" in set_cookie and "httponly" in set_cookie and "samesite=lax" in set_cookie
    assert "max-age" not in set_cookie  # not remembered: ends with the browser session
    # the browser (TestClient keeps cookies) is now logged in without any Authorization header
    assert client.get("/api/auth/me").json()["email"] == "cookie@x.co"


def test_remember_me_keeps_cookie_for_30_days(client, make_user):
    make_user("keep@x.co")
    r = client.post("/api/auth/login", data={"username": "keep@x.co", "password": "password123", "remember": "true"})
    assert r.status_code == 200
    assert f"max-age={30 * 24 * 3600}" in r.headers["set-cookie"].lower()


def test_logout_clears_cookie(client, make_user):
    make_user("bye@x.co")
    client.post("/api/auth/login", data={"username": "bye@x.co", "password": "password123"})
    assert client.get("/api/auth/me").status_code == 200
    r = client.post("/api/auth/logout")
    assert r.status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_bad_cookie_is_rejected(client):
    client.cookies.set("cs_session", "not-a-real-token")
    assert client.get("/api/auth/me").status_code == 401


def test_401_keeps_www_authenticate_header(client):
    r = client.post("/api/auth/login", data={"username": "nobody@x.co", "password": "whatever1"})
    assert r.status_code == 401
    assert r.headers.get("www-authenticate") == "Bearer"
