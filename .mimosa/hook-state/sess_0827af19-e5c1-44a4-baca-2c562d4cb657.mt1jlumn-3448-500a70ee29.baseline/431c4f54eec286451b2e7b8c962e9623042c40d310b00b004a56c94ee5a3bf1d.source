# -*- coding: utf-8 -*-
"""Unified afferent_events_per_minute_by_source."""
from __future__ import annotations

import time
from collections import defaultdict


def per_minute_by_source(events: list[dict], *, window_s: float | None = None,
                         now: float | None = None) -> dict:
    now = time.time() if now is None else now
    if window_s is None:
        times = []
        for e in events:
            t = e.get("ingested_at_unix") or e.get("occurred_at_unix")
            if isinstance(t, (int, float)):
                times.append(t)
        window_s = max(60.0, (max(times) - min(times)) if len(times) >= 2 else 60.0)
    minutes = max(window_s / 60.0, 1.0 / 60.0)
    counts: dict[str, int] = defaultdict(int)
    for e in events:
        if e.get("status") and e.get("status") != "ok":
            continue
        src = str(e.get("source") or "unknown")
        counts[src] += 1
    return {src: round(n / minutes, 4) for src, n in sorted(counts.items())}
