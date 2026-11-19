"""Serving the built website from FastAPI (production setup)."""

import pytest
from app.core.frontend import mount_frontend
from app.core.security_headers import SecurityHeadersMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def site(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>CivicSignal</title>")
    (dist / "assets" / "app-123.js").write_text("console.log('hi')")
    (dist / "favicon.svg").write_text("<svg/>")
    (tmp_path / "secret.txt").write_text("outside the website folder")

    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, https_only=True)

    @app.get("/api/ping")
    def ping():
        return {"pong": True}

    mount_frontend(app, str(dist))
    return TestClient(app)


def test_home_and_app_routes_return_the_website(site):
    for path in ("/", "/dashboard", "/some/deep/link"):
        r = site.get(path)
        assert r.status_code == 200 and "<title>CivicSignal</title>" in r.text
        assert r.headers["cache-control"] == "no-cache"


def test_files_are_served_and_hashed_assets_cached(site):
    r = site.get("/assets/app-123.js")
    assert r.status_code == 200 and "console.log" in r.text
    assert "immutable" in r.headers["cache-control"]
    assert site.get("/favicon.svg").status_code == 200


def test_api_routes_still_win_and_unknown_api_is_404(site):
    assert site.get("/api/ping").json() == {"pong": True}
    assert site.get("/api/nope").status_code == 404


def test_cannot_escape_the_website_folder(site):
    for path in ("/../secret.txt", "/assets/../../secret.txt", "/%2e%2e/secret.txt"):
        r = site.get(path)
        assert "outside the website folder" not in r.text


def test_pages_get_a_strict_but_working_csp(site):
    csp = site.get("/").headers["content-security-policy"]
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp.split("style-src")[0]
    assert "fonts.googleapis.com" in csp and "frame-ancestors 'none'" in csp
    assert site.get("/api/ping").headers["content-security-policy"].startswith("default-src 'none'")


def test_missing_build_is_a_clear_error(tmp_path):
    with pytest.raises(RuntimeError, match="build the frontend"):
        mount_frontend(FastAPI(), str(tmp_path))
