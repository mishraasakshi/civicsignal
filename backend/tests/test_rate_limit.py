"""Login / sign-up rate limiting."""

from app.core import rate_limit
from app.core.rate_limit import RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


# ---------- the limiter on its own (fake clock, no waiting) ----------


def test_limiter_allows_up_to_max_then_blocks_until_window_passes():
    clock = FakeClock()
    limiter = RateLimiter(max_events=3, window_seconds=60, clock=clock)
    assert [limiter.check_and_hit("k") for _ in range(3)] == [0, 0, 0]
    assert limiter.check_and_hit("k") == 60  # 4th: wait the full minute
    clock.now += 30
    assert limiter.check_and_hit("k") == 30  # half way: 30 s left
    clock.now += 30
    assert limiter.check_and_hit("k") == 0  # oldest events expired


def test_limiter_keys_are_independent_and_reset_works():
    limiter = RateLimiter(max_events=1, window_seconds=60, clock=FakeClock())
    assert limiter.check_and_hit("a") == 0
    assert limiter.check_and_hit("a") > 0
    assert limiter.check_and_hit("b") == 0  # another key is unaffected
    limiter.reset("a")
    assert limiter.check_and_hit("a") == 0


# ---------- through the API ----------


def _login(client, email, password):
    return client.post("/api/auth/login", data={"username": email, "password": password})


def test_five_wrong_passwords_lock_the_account_even_for_the_right_password(client, make_user):
    make_user("victim@x.co")  # real password: password123
    for _ in range(5):
        assert _login(client, "victim@x.co", "wrong-guess").status_code == 401
    r = _login(client, "victim@x.co", "password123")
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "TOO_MANY_REQUESTS"
    assert int(r.headers["Retry-After"]) > 0
    # other accounts still work
    make_user("someone@x.co")
    assert _login(client, "someone@x.co", "password123").status_code == 200


def test_successful_login_resets_the_failure_count(client, make_user):
    make_user("forgetful@x.co")
    for _ in range(4):
        _login(client, "forgetful@x.co", "wrong-guess")
    assert _login(client, "forgetful@x.co", "password123").status_code == 200
    for _ in range(4):  # 4 more mistakes are allowed again
        assert _login(client, "forgetful@x.co", "wrong-guess").status_code == 401
    assert _login(client, "forgetful@x.co", "password123").status_code == 200


def test_unknown_emails_are_limited_the_same_way(client):
    for _ in range(5):
        assert _login(client, "ghost@x.co", "whatever1").status_code == 401
    assert (
        _login(client, "ghost@x.co", "whatever1").status_code == 429
    )  # no hint the email doesn't exist


def test_one_network_cannot_try_many_accounts(client):
    for i in range(20):
        assert _login(client, f"user{i}@x.co", "whatever1").status_code == 401
    assert _login(client, "user99@x.co", "whatever1").status_code == 429


def test_sign_up_is_limited_per_network(client):
    for i in range(10):
        r = client.post(
            "/api/auth/register", json={"email": f"new{i}@x.co", "password": "longpassword"}
        )
        assert r.status_code == 201
    r = client.post("/api/auth/register", json={"email": "new10@x.co", "password": "longpassword"})
    assert r.status_code == 429


def test_limits_reset_between_tests(client, make_user):
    # the conftest clears the limiters, so earlier tests' failures don't leak in here
    assert rate_limit.failed_logins_per_email.retry_after("victim@x.co") == 0
    make_user("victim@x.co")
    assert _login(client, "victim@x.co", "password123").status_code == 200
