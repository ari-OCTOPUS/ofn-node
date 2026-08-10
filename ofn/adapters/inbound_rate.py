"""Inbound HTTP rate limiter: protect the webhook endpoint from flooding.

Lightweight, in-memory, stdlib-only. Uses a fixed-window counter per source
key (typically the remote IP or tenant name). When the limit is hit within
the window, subsequent requests are rejected with a 429-like verdict.

This is separate from the outbound rate limiter in rate_limit.py which
throttles platform publish operations. This one guards the *inbound* HTTP
surface.

Thread-safe via a single lock. No SQLite — the rate window is short (60s)
and the data is transient. Losing the counter on restart is the correct
behaviour: it resets the window, which is what you want after a reboot.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Mapping


@dataclass
class _Bucket:
    count: int = 0
    window_start: float = 0.0


@dataclass(frozen=True)
class InboundVerdict:
    allowed: bool
    remaining: int = 0
    retry_after_s: int = 0
    rule: str = ""


RULE_OK = "inbound:ok"
RULE_LIMITED = "inbound:limited"


@dataclass
class InboundRateLimiter:
    """Fixed-window rate limiter for inbound HTTP requests.

    Args:
        max_requests: Maximum requests per window per key.
        window_seconds: Length of the window in seconds.
        max_buckets: Cap on distinct keys tracked simultaneously. When
            exceeded, the oldest bucket is evicted (FIFO by window_start).
            This prevents an attacker from exhausting memory by sending
            requests with unique keys.
    """

    max_requests: int = 60
    window_seconds: int = 60
    max_buckets: int = 1024
    _buckets: dict = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def check(self, key: str, now: float | None = None) -> InboundVerdict:
        """Check whether a request from `key` should be allowed.

        `now` defaults to time.monotonic(). Injected in tests for determinism.
        """
        if now is None:
            now = time.monotonic()

        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None or (now - bucket.window_start) >= self.window_seconds:
                self._evict_if_needed()
                self._buckets[key] = _Bucket(count=1, window_start=now)
                return InboundVerdict(True, self.max_requests - 1, 0, RULE_OK)
            if bucket.count >= self.max_requests:
                elapsed = now - bucket.window_start
                retry_after = max(1, int(self.window_seconds - elapsed))
                return InboundVerdict(False, 0, retry_after, RULE_LIMITED)
            bucket.count += 1
            return InboundVerdict(
                True, self.max_requests - bucket.count, 0, RULE_OK)

    def _evict_if_needed(self) -> None:
        """Drop the oldest bucket when the cap is about to be exceeded."""
        if len(self._buckets) >= self.max_buckets:
            # Remove the bucket with the oldest window_start.
            oldest_key = min(self._buckets, key=lambda k: self._buckets[k].window_start)
            self._buckets.pop(oldest_key, None)

    def reset(self, key: str | None = None) -> None:
        """Clear bucket(s). For tests."""
        with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)

    def snapshot(self) -> Mapping[str, Mapping[str, object]]:
        """Current state of all buckets, for diagnostics."""
        with self._lock:
            return {
                k: {"count": v.count, "window_start": v.window_start}
                for k, v in self._buckets.items()
            }
