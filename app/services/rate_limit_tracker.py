"""
In-memory rate-limit tracker.

Counts API requests per (provider, model) key within sliding minute and day
windows, then computes remaining requests against known limits.
"""

import threading
import time
from collections import deque


class RateLimitTracker:
    """Thread-safe sliding-window request counter."""

    def __init__(self):
        self._lock = threading.Lock()
        # key -> deque of timestamps (float, seconds since epoch)
        self._minute_window: dict[str, deque] = {}
        self._day_window: dict[str, deque] = {}

    def record(self, key: str) -> None:
        """Record one request for the given key."""
        now = time.time()
        with self._lock:
            for window, seconds in ((self._minute_window, 60), (self._day_window, 86400)):
                if key not in window:
                    window[key] = deque()
                dq = window[key]
                dq.append(now)
                cutoff = now - seconds
                while dq and dq[0] < cutoff:
                    dq.popleft()

    def counts(self, key: str) -> dict[str, int]:
        """Return current request counts for the last minute and day."""
        now = time.time()
        with self._lock:
            rpm_dq = self._minute_window.get(key, deque())
            rpd_dq = self._day_window.get(key, deque())
            rpm = sum(1 for t in rpm_dq if t >= now - 60)
            rpd = sum(1 for t in rpd_dq if t >= now - 86400)
        return {"rpm": rpm, "rpd": rpd}

    def remaining(self, key: str, rpm_limit: int | None, rpd_limit: int | None) -> dict:
        """Return remaining requests for the given limits."""
        c = self.counts(key)
        return {
            "remaining_rpm": max(0, rpm_limit - c["rpm"]) if rpm_limit is not None else None,
            "remaining_rpd": max(0, rpd_limit - c["rpd"]) if rpd_limit is not None else None,
            "used_rpm": c["rpm"],
            "used_rpd": c["rpd"],
            "limit_rpm": rpm_limit,
            "limit_rpd": rpd_limit,
        }


# Singleton shared across the app process
tracker = RateLimitTracker()
