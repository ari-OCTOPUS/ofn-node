#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_hub_shadow_rollout.py — Phase 6 dual-read shadow harness."""
from __future__ import annotations

import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parents[1]
for _p in (str(_OPS), str(_OPS / "tests"), str(_OPS / "conversation_hub")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import harness  # noqa: E402
ENV = harness.setup("hub-shadow-rollout")


def t_shadow_runs_both_paths_safely():
    from conversation_hub import shadow_rollout as SR
    reads = SR.run_shadow(("وضعیت چیست؟",))
    assert len(reads) == 1
    r = reads[0]
    # هر دو مسیر باید external_effect=False (invariant: observe+propose only)
    assert r.hub_external_effect is False
    assert r.both_safe is True


def t_summarize_all_safe():
    from conversation_hub import shadow_rollout as SR
    rep = SR.summarize(SR.run_shadow(("هدف چیست؟", "موانع چیست؟")))
    assert rep.n_probes == 2
    assert rep.all_safe is True
    assert 0.0 <= rep.mean_overlap <= 1.0
    txt = SR.format_report(rep)
    assert "Shadow Rollout" in txt


def t_overlap_metric():
    from conversation_hub.shadow_rollout import _overlap
    assert _overlap("", "") == 1.0
    assert _overlap("a b c", "") == 0.0
    assert _overlap("a b c", "a b c") == 1.0
    assert 0 < _overlap("a b c d", "a b x y") < 1


def t_write_jsonl_appends():
    import tempfile
    from conversation_hub import shadow_rollout as SR
    rep = SR.summarize(SR.run_shadow(("وضعیت چیست؟",)))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "shadow.jsonl"
        SR.write_jsonl(rep, p)
        SR.write_jsonl(rep, p)
        lines = p.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2   # append-only


TESTS = [
    t_shadow_runs_both_paths_safely,
    t_summarize_all_safe,
    t_overlap_metric,
    t_write_jsonl_appends,
]

if __name__ == "__main__":
    failed = 0
    for _t in TESTS:
        try:
            _t()
            print(f"  PASS  {_t.__name__}")
        except Exception as exc:
            import traceback
            print(f"  FAIL  {_t.__name__}: {exc}")
            traceback.print_exc()
            failed += 1
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(failed)
