#!/usr/bin/env python3
"""Offline, hermetic test for M2 (now_moves/staleness_stamp).

Stdlib-only · no network · NO live reads (every case passes a synthetic
innervation `check`, so live innervation/opslib is never imported). Verifies:
dead→🔴 · slow→🟡 · healthy unchanged · never-upgrade · unmatched passthrough ·
bare-glyph contract · input not mutated · stamp_summary wrapping.
Runs standalone (exit 0/1) per the run_all.py convention; also exposes test_*.
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("ORG_ROOT", tempfile.mkdtemp(prefix="m2_stale_"))
os.environ.pop("OCTOPUS_WIRE_STALENESS_STAMP", None)

HERE = Path(__file__).resolve().parent
OPS = HERE.parent
for _p in (str(OPS / "now_moves"), str(OPS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import staleness_stamp as P                              # noqa: E402


def _check(*organs):
    return {"organs": list(organs)}


def _org(name, status, age_min, connected):
    return {"id": "x", "name": name, "status": status,
            "age_min": age_min, "sla_min": 30, "connected": connected}


def test_dead_forces_red():
    parts = [{"name": "🧠 مغز", "status": "🟢", "detail": "هم‌آهنگی 88٪"}]
    chk = _check(_org("🧠 مغزِ مرکزی", "🔴 نقطهٔ مرده", 2149.8, False))
    out = P.stamp(parts, check=chk)
    assert out[0]["status"] == "🔴" and out[0]["stale"] is True, out
    assert out[0]["age_min"] == 2149.8, out
    assert "کهنه" in out[0]["detail"] and "88٪" in out[0]["detail"], out
    print("  ok dead organ            -> cell 🟢->🔴 + age in detail")


def test_bare_glyph_contract():
    # status must be EXACTLY a bare glyph (render.py matches "🔴"/"🟡" exactly)
    parts = [{"name": "🧠 مغز", "status": "🟢"}]
    chk = _check(_org("🧠 مغزِ مرکزی", "🔴 نقطهٔ مرده", 2000, False))
    out = P.stamp(parts, check=chk)
    assert out[0]["status"] == "🔴", repr(out[0]["status"])   # not "🔴 کهنه"
    print("  ok bare-glyph contract   -> status is exactly '🔴' (leg-rank safe)")


def test_healthy_unchanged():
    parts = [{"name": "🧠 مغز", "status": "🟢", "detail": "د"}]
    chk = _check(_org("🧠 مغزِ مرکزی", "🟢 عصب‌دار", 2.0, True))
    out = P.stamp(parts, check=chk)
    assert out[0]["status"] == "🟢" and "stale" not in out[0], out
    print("  ok healthy organ         -> cell unchanged")


def test_slow_downgrades_green():
    parts = [{"name": "🧠 مغز", "status": "🟢", "detail": "د"}]
    chk = _check(_org("🧠 مغزِ مرکزی", "🟡 کند", 70.0, True))
    out = P.stamp(parts, check=chk)
    assert out[0]["status"] == "🟡" and out[0]["stale"] is True, out
    print("  ok slow organ            -> cell 🟢->🟡")


def test_never_upgrades():
    parts = [{"name": "🧠 مغز", "status": "🔴", "detail": "د"}]     # already worse
    chk = _check(_org("🧠 مغزِ مرکزی", "🟡 کند", 70.0, True))       # organ only slow
    out = P.stamp(parts, check=chk)
    assert out[0]["status"] == "🔴", out                          # must NOT upgrade to 🟡
    print("  ok never upgrades        -> 🔴 cell stays 🔴 vs slow organ")


def test_unmatched_passthrough():
    parts = [{"name": "⚕️ دکتر", "status": "🟢", "detail": "د"}]   # no matching organ
    chk = _check(_org("🧠 مغزِ مرکزی", "🔴 نقطهٔ مرده", 2000, False))
    out = P.stamp(parts, check=chk)
    assert out[0]["status"] == "🟢" and "stale" not in out[0], out
    print("  ok unmatched cell        -> passes through unchanged")


def test_input_not_mutated():
    parts = [{"name": "🧠 مغز", "status": "🟢"}]
    chk = _check(_org("🧠 مغزِ مرکزی", "🔴 نقطهٔ مرده", 2000, False))
    P.stamp(parts, check=chk)
    assert parts[0]["status"] == "🟢", "read-only: input must not be mutated"
    print("  ok read-only             -> input list/dicts not mutated")


def test_stamp_summary_wraps():
    summ = {"parts": [{"name": "🧠 مغز", "status": "🟢"}], "n_proposals": 2}
    chk = _check(_org("🧠 مغزِ مرکزی", "🔴 نقطهٔ مرده", 2000, False))
    out = P.stamp_summary(summ, check=chk)
    assert out["parts"][0]["status"] == "🔴" and out["n_proposals"] == 2, out
    print("  ok stamp_summary         -> wraps summary['parts'], keeps siblings")


def _run():
    tests = [test_dead_forces_red, test_bare_glyph_contract, test_healthy_unchanged,
             test_slow_downgrades_green, test_never_upgrades, test_unmatched_passthrough,
             test_input_not_mutated, test_stamp_summary_wraps]
    print("test_staleness_stamp (M2) — offline, hermetic")
    for t in tests:
        t()
    print(f"PASS {len(tests)}/{len(tests)}")


if __name__ == "__main__":
    try:
        _run()
    except AssertionError as e:
        print("FAIL:", e); sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print("ERROR:", type(e).__name__, e); sys.exit(1)
    sys.exit(0)
