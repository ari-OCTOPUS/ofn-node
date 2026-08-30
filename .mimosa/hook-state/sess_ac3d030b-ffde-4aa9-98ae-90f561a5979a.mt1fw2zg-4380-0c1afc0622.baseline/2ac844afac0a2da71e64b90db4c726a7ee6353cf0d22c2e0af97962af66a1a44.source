"""Offline test: v0.4.4 EVENT_TYPES append-only extension (verdict V2, 2026-07-07).

Checks: (1) MONEY_ATTRIBUTION appends and the hash chain verifies; (2) mixing with
old types keeps the chain; (3) the set stays CLOSED - unknown types still rejected.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ledger"))

from ledger import EVENT_TYPES, Ledger  # noqa: E402


def main() -> int:
    assert "MONEY_ATTRIBUTION" in EVENT_TYPES
    tmp = Path(tempfile.mkdtemp(prefix="money-ev-")) / "ledger.jsonl"
    lg = Ledger(str(tmp))
    lg.append("NOTE", {"subtype": "EXPERIENCE", "x": 1}, actor="test")
    lg.append("MONEY_ATTRIBUTION", {
        "attribution_id": "LEAD-20260707-001", "state": "PROPOSAL",
        "amount_aud": 0.0, "cell": "lead.doer"}, actor="reconcile-job")
    lg.append("APPROVAL", {"origin": {"loop": "human"}}, actor="approval-queue")
    ok, msg = lg.verify()
    assert ok, msg
    rows = list(lg.iter_events())
    assert rows[-2]["type"] == "MONEY_ATTRIBUTION", rows[-2]
    print("  ok: MONEY_ATTRIBUTION appended, chain verified across mixed types")

    try:
        lg.append("TOTALLY_NEW_TYPE", {}, actor="test")
        print("FAIL: unknown type was accepted - closed set broken")
        return 1
    except ValueError:
        print("  ok: unknown type still rejected (set stays closed)")
    ok, msg = lg.verify()
    assert ok, msg
    print("OK: money_event_test (3 checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
