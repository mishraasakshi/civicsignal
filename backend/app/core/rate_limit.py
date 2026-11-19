"""Simple in-memory rate limiting for login and sign-up (no extra packages).

How it works: for each key (an email or an IP address) we remember the times of recent
events. If there are too many inside the time window, the request is refused with 429.

Limits (see settings):
- failed logins per email: 5 per 15 minutes -> that email is locked until the oldest failure expires
- login attempts per IP:   20 per minute   -> stops one machine trying many emails
- sign-ups per IP:         10 per hour     -> stops mass fake accounts

Limitation: the counts live in this process's memory. That is fine for one server; with
several servers (or after a restart) the counts are not shared - then use Redis instead.
"""

import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import HTTPException, status


class RateLimiter:
    def __init__(
        self, max_events: int, window_seconds: float, clock: Callable[[], float] = time.monotonic
    ):
        self.max_events = max_events
        self.window = window_seconds
        self.clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        events = self._events[key]
        while events and now - events[0] >= self.window:
            events.popleft()
        return events

    def retry_after(self, key: str) -> int:
        """Seconds until a new event is allowed for this key (0 = allowed now)."""
        with self._lock:
            now = self.clock()
            events = self._prune(key, now)
            if len(events) < self.max_events:
                return 0
            return max(1, math.ceil(self.window - (now - events[0])))

    def hit(self, key: str) -> None:
        """Record one event for this key."""
        with self._lock:
            now = self.clock()
            self._prune(key, now).append(now)

    def check_and_hit(self, key: str) -> int:
        """Record an event if allowed. Returns 0 if allowed, else seconds to wait (nothing recorded)."""
        with self._lock:
            now = self.clock()
            events = self._prune(key, now)
            if len(events) >= self.max_events:
                return max(1, math.ceil(self.window - (now - events[0])))
            events.append(now)
            return 0

    def reset(self, key: str) -> None:
        with self._lock:
            self._events.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


def too_many(retry_after: int, what: str) -> HTTPException:
    minutes = max(1, math.ceil(retry_after / 60))
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        detail=f"too many {what}. Please try again in about {minutes} minute{'s' if minutes != 1 else ''}.",
        headers={"Retry-After": str(retry_after)},
    )


# The app's limiters (tests call .clear() between tests)
failed_logins_per_email = RateLimiter(max_events=5, window_seconds=15 * 60)
logins_per_ip = RateLimiter(max_events=20, window_seconds=60)
signups_per_ip = RateLimiter(max_events=10, window_seconds=60 * 60)


def clear_all() -> None:
    for limiter in (failed_logins_per_email, logins_per_ip, signups_per_ip):
        limiter.clear()
