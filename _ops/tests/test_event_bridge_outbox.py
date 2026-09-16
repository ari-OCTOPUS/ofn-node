#!/usr/bin/env python3
"""Lane C — event_bridge must not suppress a failed alert for 24h."""
from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]


class _Center:
    def __init__(self, ok: bool):
        self.ok = ok
        self.calls = 0

    def push_alert(self, text: str) -> bool:
        self.calls += 1
        return self.ok


def _fresh():
    root = Path(tempfile.mkdtemp(prefix="eb-outbox-"))
    os.environ["ORG_ROOT"] = str(root)
    os.environ["OPS_DIR"] = str(root / "_ops")
    os.environ["OCTOPUS_STATE_DIR"] = str(root / "_ops" / "state")
    os.environ["OCTOPUS_WIRE_EVENT_BRIDGE"] = "1"
    # هر تست root جدای خودش دارد؛ ماژول‌های env-driven باید تازه شوند وگرنه
    # opslib کش‌شده به root قبلی می‌چسبد و تست به فایل اشتباه می‌زند.
    for _m in [k for k in list(sys.modules)
               if k in ("opslib", "event_bridge") or k.startswith("opslib.")]:
        sys.modules.pop(_m, None)
    sys.path.insert(0, str(_OPS))
    sys.path.insert(0, str(_OPS / "budget"))
    sys.path.insert(0, str(_OPS / "telegram_center"))
    import event_bridge
    eb = importlib.reload(event_bridge)
    return eb, root


def _seed_alert(root: Path, text: str = "⚠️ critical incident broken link") -> str:
    alerts = root / "_ops" / "governor" / "governor-alerts.md"
    alerts.parent.mkdir(parents=True, exist_ok=True)
    alerts.write_text("## 2026-08-21 00:00 (alert)\n" + f"- {text}\n", encoding="utf-8")
    return text


def _pending_rows(root: Path) -> list:
    p = root / "_ops" / "state" / "telegram" / "event-bridge-pending.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _outbox_rows(root: Path) -> list:
    p = root / "_ops" / "state" / "telegram" / "event-bridge-outbox.jsonl"
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text("utf-8").splitlines() if x.strip()]


def _seen(root: Path) -> dict:
    p = root / "_ops" / "state" / "telegram" / "event-bridge-cursor.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text("utf-8"))
    return d.get("pushed_signatures") or {}


def t_a_failed_push_not_marked_seen_and_queued_for_retry():
    eb, root = _fresh()
    text = _seed_alert(root)
    center = _Center(ok=False)
    out = eb.beat(center=center)
    assert out["pushed"] == 0
    assert text not in "".join(_seen(root).keys()), "failed push must not be marked seen"
    pending = _pending_rows(root)
    assert len(pending) == 1 and pending[0]["key"] == eb._sign(text)
    ob = _outbox_rows(root)
    assert ob and any(r["state"] == "DELIVERY_FAILED" for r in ob)


def t_b_retry_on_next_beat_then_mark_seen():
    eb, root = _fresh()
    text = _seed_alert(root)
    assert eb.beat(center=_Center(ok=False))["pushed"] == 0
    center = _Center(ok=True)
    out = eb.beat(center=center)
    assert out["pushed"] == 1
    assert eb._sign(text) in _seen(root), "successful retry must mark seen"
    assert _pending_rows(root) == []
    ob = _outbox_rows(root)
    assert any(r["state"] == "CONFIRMED" for r in ob)


def t_c_after_max_attempts_moves_to_dlq():
    eb, root = _fresh()
    text = _seed_alert(root)
    for _ in range(3):
        assert eb.beat(center=_Center(ok=False))["pushed"] == 0
    assert _pending_rows(root) == [], "exhausted pending must move to DLQ"
    ob = _outbox_rows(root)
    assert any(r["state"] == "DLQ" for r in ob), ob
    assert eb._sign(text) not in _seen(root)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\ntest_event_bridge_outbox: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
