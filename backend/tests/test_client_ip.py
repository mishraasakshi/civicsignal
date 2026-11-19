"""The visitor's real IP behind proxies (so rate limits count each visitor separately)."""

from app.core.client_ip import client_ip
from starlette.requests import Request


def request(peer="10.0.0.9", xff=None) -> Request:
    headers = [(b"x-forwarded-for", xff.encode())] if xff else []
    return Request({"type": "http", "headers": headers, "client": (peer, 1234)})


def test_no_proxy_uses_the_direct_connection():
    assert (
        client_ip(request(xff="1.2.3.4"), hops=0) == "10.0.0.9"
    )  # header ignored when not trusted


def test_one_trusted_proxy_takes_the_last_entry():
    assert client_ip(request(xff="203.0.113.7"), hops=1) == "203.0.113.7"


def test_a_faked_header_cannot_choose_the_address():
    # the visitor sends "X-Forwarded-For: 6.6.6.6"; the proxy appends the real address
    assert client_ip(request(xff="6.6.6.6, 203.0.113.7"), hops=1) == "203.0.113.7"


def test_two_proxies():
    assert client_ip(request(xff="6.6.6.6, 203.0.113.7, 10.1.1.1"), hops=2) == "203.0.113.7"


def test_missing_header_falls_back_to_the_connection():
    assert client_ip(request(), hops=1) == "10.0.0.9"
