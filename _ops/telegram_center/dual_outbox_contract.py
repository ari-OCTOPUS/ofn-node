#!/usr/bin/env python3
"""Label Telegram outbox paths as SoT vs non-SoT (C05). No I/O merge."""
from __future__ import annotations

from pathlib import Path

OPS = Path(__file__).resolve().parents[1]
SOT_OUTBOX = OPS / "state" / "telegram" / "loop" / "outbox"
SOT_EVENTS = OPS / "state" / "telegram" / "loop" / "events"
CANARY_GLOB = "*-canary*.sqlite3"
CANARY_DIR = OPS / "state" / "telegram"


def classify(path: str | Path) -> dict:
    p = Path(path).resolve()
    try:
        rel = p.relative_to(OPS.resolve())
    except ValueError:
        rel = p
    s = str(p).replace("\\", "/").lower()
    if "/state/telegram/loop/outbox" in s or p == SOT_OUTBOX.resolve() or SOT_OUTBOX.resolve() in p.parents or p.parent == SOT_OUTBOX.resolve():
        return {"path": str(p), "class": "SOT_DURABLE_OUTBOX", "merge_with_canary": False}
    if "/state/telegram/loop/events" in s:
        return {"path": str(p), "class": "SOT_DURABLE_EVENTS", "merge_with_canary": False}
    if "canary" in p.name.lower() and p.suffix.lower() in {".sqlite3", ".sqlite", ".db"}:
        return {"path": str(p), "class": "NON_SOT_CANARY_SQLITE", "merge_with_canary": False}
    if "canary" in s and "telegram" in s:
        return {"path": str(p), "class": "NON_SOT_CANARY_SIDEPATH", "merge_with_canary": False}
    return {"path": str(p), "class": "UNKNOWN", "merge_with_canary": False, "rel": str(rel)}


def assert_not_merged_policy() -> dict:
    """Documentation-level invariant: SoT and canary classes never merge."""
    sot = classify(SOT_OUTBOX)
    example_canary = CANARY_DIR / "a18-owner-canary-rate-limit.sqlite3"
    can = classify(example_canary)
    assert sot["class"].startswith("SOT_"), sot
    assert can["class"].startswith("NON_SOT_"), can
    assert sot["merge_with_canary"] is False and can["merge_with_canary"] is False
    return {"ok": True, "sot": sot, "canary_example": can}

# G08 — additional non-SoT / adjacent surfaces (never merge into durable SoT)
TRIPLE_SURFACES = {
    "SOT_DURABLE_OUTBOX": SOT_OUTBOX,
    "SOT_DURABLE_EVENTS": SOT_EVENTS,
    "NON_SOT_CANARY_SQLITE": CANARY_DIR / "a18-owner-canary-rate-limit.sqlite3",
}


def classify_surface(path: str | Path) -> dict:
    """Classify durable vs canary vs other telegram state paths."""
    base = classify(path)
    s = str(Path(path)).replace("\\", "/").lower()
    if "/event-bridge" in s or s.endswith("/event-bridge"):
        base["class"] = "NON_SOT_EVENT_BRIDGE"
        base["merge_with_canary"] = False
        base["merge_into_durable_sot"] = False
    elif "/urgent" in s:
        base["class"] = "NON_SOT_URGENT_SIDEPATH"
        base["merge_with_canary"] = False
        base["merge_into_durable_sot"] = False
    else:
        base.setdefault("merge_into_durable_sot", False)
    return base
