#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pass 1 ladder + surfaces. Not registered in run_all.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_OPS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_OPS))

from loops import families, ladder, pass1_readonly  # noqa: E402


def t_twelve_families_twenty_four_discovery():
    assert len(families.FAMILIES) == 12
    assert len(families.DISCOVERY) == 24
    assert len(families.BYTE_SPRINT) == 13


def t_l6_requires_both_surfaces():
    assert ladder.require_surfaces("/status", "/miniapp") is True
    assert ladder.require_surfaces("UNROUTED", "/miniapp") is False
    lv = {r: True for r in ladder.RUNGS}
    assert ladder.stuck_at(lv) == "L6_COMPLETE"
    lv["owner_visible"] = False
    assert ladder.stuck_at(lv) == "L6_OWNER_VISIBLE"
    lv["tested"] = False
    assert ladder.stuck_at(lv) == "L4_TESTED"
    lv2 = {r: True for r in ladder.RUNGS}
    lv2["owner_visible"] = False
    assert ladder.terminal(lv2) == "READY_FOR_OWNER"


def t_pass1_writes_jsonl_without_unlocking_wave1():
    s = pass1_readonly.run()
    assert "wave1_unlocked" in s
    assert s["n_families"] == 12
    p = Path(s["jsonl"])
    lines = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    fams = [r for r in lines if r.get("kind") == "family"]
    discs = [r for r in lines if r.get("kind") == "discovery"]
    assert len(fams) == 12 and len(discs) == 24
    for r in fams:
        assert "telegram_surface" in r and "miniapp_route" in r
        assert "budget" in r and r["budget"]["max_retries"] == 3
        if r.get("can_close"):
            assert r["levels"].get("owner_visible") is True


if __name__ == "__main__":
    failed = 0
    for n, f in sorted((n, f) for n, f in globals().items() if n.startswith("t_")):
        try:
            f(); print(f"  OK  {n}")
        except Exception as e:
            failed += 1
            print(f"  FAIL {n}: {type(e).__name__}: {e}")
    sys.exit(1 if failed else 0)
