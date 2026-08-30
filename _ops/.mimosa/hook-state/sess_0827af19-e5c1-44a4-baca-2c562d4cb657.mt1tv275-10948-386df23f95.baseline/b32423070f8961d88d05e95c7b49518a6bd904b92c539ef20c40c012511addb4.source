#!/usr/bin/env python3
"""Lane E root cause — self_insight.card() must never run the 130s full-tree scan."""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))


def _fresh_root():
    root = Path(tempfile.mkdtemp(prefix="si-card-"))
    (root / "state").mkdir(parents=True, exist_ok=True)
    return root


def _journal(root: Path, claims=("فرضیهٔ تستی",)) -> None:
    hyps = [{"id": "test:1", "rule": "test", "subject": "s", "claim": c,
             "mechanism": [], "predicted_observation": {}, "falsifier": "",
             "confidence": 0.5, "confidence_why": "x", "impact": 1, "cost": "cheap",
             "rank": 0.5, "cheapest_test": ""} for c in claims]
    entry = {"schema": "self-insight.v1", "ts": time.time(), "hypotheses": hyps,
             "calibration": {"previous_hypotheses": 0, "measured": 0,
                             "resolved": 0, "resolution_rate": None}}
    (root / "state" / "self-insight.jsonl").write_text(
        json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")


def t_a_card_without_journal_never_runs_scan():
    import self_insight as si
    root = _fresh_root()

    def boom(*a, **k):
        raise AssertionError("card() must not run the full scan")
    old_run = si.run
    si.run = boom
    try:
        t0 = time.time()
        out = si.card(root=root)
        assert time.time() - t0 < 3, "card must be cheap"
    finally:
        si.run = old_run
    assert "اجرا نشده" in out, out


def t_b_card_reads_journal_without_running_scan():
    import self_insight as si
    root = _fresh_root()
    _journal(root, claims=("فرضیهٔ تستی از journal",))

    def boom(*a, **k):
        raise AssertionError("card() must not run the full scan")
    old_run = si.run
    si.run = boom
    try:
        t0 = time.time()
        out = si.card(root=root)
        assert time.time() - t0 < 3, "card must be cheap"
    finally:
        si.run = old_run
    assert "فرضیهٔ تستی از journal" in out, out


def t_c_capability_registry_render_of_self_insight_is_fast():
    import capability_registry as cr
    t0 = time.time()
    out = cr.render("self_insight")
    dt = time.time() - t0
    assert dt < 10, f"render took {dt:.1f}s"
    assert isinstance(out, str) and out.strip()


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
    print(f"\ntest_self_insight_card_cheap: {len(tests) - failed}/{len(tests)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
