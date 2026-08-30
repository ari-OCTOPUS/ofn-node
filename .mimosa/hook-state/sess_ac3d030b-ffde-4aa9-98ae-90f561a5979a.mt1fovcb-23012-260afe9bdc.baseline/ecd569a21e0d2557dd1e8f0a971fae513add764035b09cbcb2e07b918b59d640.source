"""Smoke test for the Phase-0 ledger. Pure stdlib; run: python tests/smoke_test.py

Exercises: append (all actors), read/tail/filter, hash-chain verification,
rejection of unknown event types, and tamper detection.
Exit code 0 = pass, 1 = fail.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# make ../ledger importable whether run from repo root or tests/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ledger"))

from ledger import Ledger  # noqa: E402


def main() -> int:
    tmp = Path(tempfile.mkdtemp()) / "ledger.jsonl"
    lg = Ledger(tmp)

    # 1) append a realistic sequence
    lg.append("HEARTBEAT", {"uptime_s": 0}, actor="guardian")
    lg.append("OBSERVE", {"path": "notes/idea.md", "op": "modified"}, actor="watcher")
    lg.append("INDEX", {"path": "notes/idea.md", "tokens": 812}, actor="indexer")
    lg.append("PROPOSAL",
              {"idea": "route nightly digest to Haiku tier",
               "confidence": 0.4, "kill_criteria": "cost > $2/day"},
              actor="creativity")
    lg.append("METRIC", {"acceptance_rate": 0.66}, actor="doctor")
    assert len(lg.tail(10)) == 5, "expected 5 records"

    # 2) filters
    assert len(lg.filter(actor="creativity")) == 1
    assert len(lg.filter(event_type="HEARTBEAT")) == 1

    # 3) unknown event type must be rejected (a buggy agent cannot pollute memory)
    try:
        lg.append("DELETE_EVERYTHING", {})
        print("FAIL: unknown event type was accepted")
        return 1
    except ValueError:
        pass

    # 4) chain verifies clean
    ok, msg = lg.verify()
    assert ok, f"fresh ledger failed verify: {msg}"

    # 5) tamper detection: hand-edit a line, expect verify() to catch it
    lines = tmp.read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1].replace("modified", "deleted")  # silent edit to history
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ok, msg = Ledger(tmp).verify()
    assert not ok, "tamper went undetected"

    print("PASS: ledger append/read/filter/verify/tamper-detection all OK")
    print(f"      (tamper correctly reported as: {msg})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
