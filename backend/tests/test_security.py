"""Production safety: startup checks, security headers, docs toggle, safe validation errors."""

from types import SimpleNamespace

import pytest
from app.core.production_checks import enforce, find_problems

GOOD = {
    "ENVIRONMENT": "production",
    "JWT_SECRET_KEY": "x" * 48,
    "DATABASE_URL": "postgresql://civicuser:Str0ng-Unique-Pass@db.internal:5432/civicsignal",
    "DATABASE_READONLY_URL": "postgresql://civic_readonly:An0ther-Strong-Pass@db.internal:5432/civicsignal",
    "CORS_ORIGINS": ["https://civicsignal.example.edu"],
}


def settings(**changes):
    return SimpleNamespace(**{**GOOD, **changes})


def test_good_production_settings_pass():
    assert find_problems(settings()) == []
    enforce(settings())  # does not raise


@pytest.mark.parametrize(
    "changes, expected",
    [
        ({"JWT_SECRET_KEY": "civicsignal-local-secret-key-2026"}, "published in this repository"),
        ({"JWT_SECRET_KEY": "short"}, "shorter than 32"),
        (
            {"DATABASE_URL": "postgresql://civicuser:civicpassword@db:5432/civicsignal"},
            "DATABASE_URL uses a default password",
        ),
        (
            {"DATABASE_READONLY_URL": "postgresql://civic_readonly:readonlypassword@db/x"},
            "DATABASE_READONLY_URL",
        ),
        ({"CORS_ORIGINS": ["*"]}, "'*'"),
        ({"CORS_ORIGINS": ["http://civicsignal.example.edu"]}, "not https"),
    ],
)
def test_unsafe_production_settings_refuse_to_start(changes, expected):
    with pytest.raises(RuntimeError) as err:
        enforce(settings(**changes))
    assert expected in str(err.value)


def test_development_only_warns(caplog):
    enforce(
        settings(
            ENVIRONMENT="development",
            JWT_SECRET_KEY="short",
            CORS_ORIGINS=["http://localhost:5173"],
        )
    )
    assert "shorter than 32" in caplog.text


def test_localhost_http_is_fine():
    assert (
        find_problems(settings(CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]))
        == []
    )


def test_api_responses_have_security_headers(client):
    h = client.get("/health").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["referrer-policy"] == "strict-origin-when-cross-origin"
    assert h["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
    assert "camera=()" in h["permissions-policy"]


def test_docs_page_gets_a_policy_that_lets_swagger_load(client):
    r = client.get("/docs")  # tests run with ENVIRONMENT=development, so docs are on
    assert r.status_code == 200
    assert "cdn.jsdelivr.net" in r.headers["content-security-policy"]


def test_validation_errors_never_echo_the_password(client):
    secret = "my-very-secret-password-" + "x" * 80  # too long -> 422
    r = client.post("/api/auth/register", json={"email": "a@b.co", "password": secret})
    assert r.status_code == 422
    assert "password" in r.json()["error"]["message"]  # says which field
    assert secret not in r.text  # but never what was typed
