#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_mission_reconcile_step1 — آشتیِ دو ماشینِ mission، قدمِ ۱ (۰۷-۳۱).

دو دنیای موازی: Genome ِ ۱۲وضعیتی (بدونِ قاعدهٔ گذار — done→created قانونی بود!)
و قراردادِ canonical ِ ۶وضعیتی (گذارِ اجباری). قدمِ ۱: (الف) Genome جدولِ گذار
گرفت با حالتِ annotate-first — غیرقانونی ثبت می‌شود ولی بلاک نمی‌شود تا رفتارِ
زندهٔ تلگرام نشکند و داده جمع شود؛ (ب) واژگانِ نگاشتِ ۱۲→۶ در خودِ
mission_contract؛ (ج) مصرف‌کنندهٔ واقعی: snapshot دنیای Genome را هم با زبانِ
canonical گزارش می‌کند. همه‌چیز در tmp.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="mrec-")).resolve()
os.environ["ORG_ROOT"] = str(_TMP)
os.environ["OPS_DIR"] = str(_TMP / "_ops")
os.environ["OCTOPUS_STATE_DIR"] = str(_TMP / "_ops" / "state")
(_TMP / "_ops" / "state").mkdir(parents=True, exist_ok=True)

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "telegram_center")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib            # noqa: E402
import mission as gm     # noqa: E402 — Mission Genome
import mission_contract as mc  # noqa: E402

assert str(opslib.STATE_DIR).startswith(str(_TMP)), opslib.STATE_DIR
assert str(gm._STATE_DIR).startswith(str(_TMP)), gm._STATE_DIR


def t_a_legal_transition_stays_clean():
    m = gm.create_mission("تستِ گذارِ قانونی — کد را چک کن", source="test")
    assert m and m["state"] == "created", m
    out = gm.set_state(m["id"], "planned")
    assert out["state"] == "planned", out
    assert "illegal_transitions" not in out, out


def t_b_illegal_transition_is_annotated_not_blocked():
    """annotate-first: تلگرامِ زنده نمی‌شکند ولی گذارِ وحشی دیگر نامرئی نیست."""
    m = gm.create_mission("تستِ گذارِ غیرقانونی — دیف بده", source="test")
    gm.set_state(m["id"], "planned")
    gm.set_state(m["id"], "tested")
    gm.set_state(m["id"], "reviewed")
    gm.set_state(m["id"], "approved")
    gm.set_state(m["id"], "applied")
    gm.set_state(m["id"], "done")
    out = gm.set_state(m["id"], "created")          # وحشی: done→created
    assert out is not None and out["state"] == "created", "بلاک شد — annotate-first نقض"
    ill = out.get("illegal_transitions") or []
    assert ill and ill[-1]["from"] == "done" and ill[-1]["to"] == "created", ill


def t_c_can_transition_12_is_failclosed_on_unknown():
    assert gm.can_transition_12("created", "planned") is True
    assert gm.can_transition_12("done", "created") is False
    assert gm.can_transition_12("ghost", "planned") is False


def t_d_every_genome_state_maps_to_a_valid_canonical_state():
    for s in gm._ALLOWED_STATES:
        canon = mc.genome_to_canonical(s)
        assert canon in mc.STATUS, (s, canon)
    assert mc.genome_to_canonical("awaiting_owner") == "needs_approval"
    assert mc.genome_to_canonical("reverted") == "failed"
    assert mc.genome_to_canonical("مجهول") == "blocked"      # ناشناخته = fail-up


def t_e_snapshot_reports_the_genome_world_in_canonical_vocab():
    from unified_control import snapshot
    old = snapshot.STATE
    box = _TMP / "snapstate"
    (box / "telegram" / "missions").mkdir(parents=True, exist_ok=True)
    (box / "telegram" / "missions" / "missions.json").write_text(json.dumps({
        "missions": [{"id": "M-1", "state": "awaiting_owner"},
                     {"id": "M-2", "state": "done"},
                     {"id": "M-3", "state": "tested"}]}, ensure_ascii=False), "utf-8")
    try:
        snapshot.STATE = box
        s = snapshot.build(now=1_785_400_000.0)
        g = s["genome_missions"]
        assert g["total"] == 3, g
        assert g["awaiting_owner"] == 1, g
        assert g["counts"] == {"needs_approval": 1, "done": 1, "running": 1}, g
    finally:
        snapshot.STATE = old


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("t_")]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  ✅ {name}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {name}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  💥 {name}: {type(e).__name__}: {e}")
    print(f"\n{'✅' if not failed else '❌'} test_mission_reconcile_step1: "
          f"{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(1 if failed else 0)
