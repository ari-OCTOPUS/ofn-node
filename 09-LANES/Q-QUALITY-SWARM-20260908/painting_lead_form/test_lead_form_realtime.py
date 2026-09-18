"""Realtime store-only painting lead. baseline_action must stay 0."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lead_form import BASELINE_ACTION, list_leads, submit_lead  # noqa: E402


def test_realtime_lead_persists(tmp_path: Path) -> None:
    store = tmp_path / "leads.jsonl"
    before = list_leads(store)
    assert before == []
    rec = submit_lead(
        store,
        {
            "name": "Test Lead",
            "contact": "0400000000",
            "suburb": "Carlingford",
            "message": "interior repaint 3BR",
        },
        now=datetime(2026, 9, 8, 5, 30, tzinfo=timezone.utc),
    )
    after = list_leads(store)
    assert len(after) == 1
    assert after[0]["name"] == "Test Lead"
    assert after[0]["baseline_action"] == 0
    assert after[0]["baseline_action"] == BASELINE_ACTION
    assert rec["sent"] is False
    assert rec["paid"] is False
    assert rec["ts"] == "2026-09-08T05:30:00Z"
    raw = store.read_text(encoding="utf-8").strip()
    assert json.loads(raw)["name"] == "Test Lead"


def test_empty_name_rejected(tmp_path: Path) -> None:
    store = tmp_path / "leads.jsonl"
    try:
        submit_lead(store, {"name": "  "})
    except ValueError as e:
        assert "name-required" in str(e)
    else:
        raise AssertionError("empty name must fail closed")
    assert list_leads(store) == []


if __name__ == "__main__":
    import tempfile

    failed = 0
    with tempfile.TemporaryDirectory() as d:
        try:
            test_realtime_lead_persists(Path(d))
            print("PASS test_realtime_lead_persists")
        except Exception as e:
            failed += 1
            print("FAIL test_realtime_lead_persists", e)
    with tempfile.TemporaryDirectory() as d:
        try:
            test_empty_name_rejected(Path(d))
            print("PASS test_empty_name_rejected")
        except Exception as e:
            failed += 1
            print("FAIL test_empty_name_rejected", e)
    raise SystemExit(1 if failed else 0)
