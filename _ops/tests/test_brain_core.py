#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_brain_core.py — C7 Slice 4: ریشهٔ ترکیبِ ضربانِ سایه (production-wired shadow).

پوشش (مأموریت Slice 4):
  1. production composition adapterهای **واقعی** را import می‌کند (SENSE/RECORD/THINK/HEAL)
  2. **صفر ACT registration** در سایه
  3. فلگ خاموش → composition = None (harness، صفر اثر)
  4. tickِ سایه adapterهای read-only را اجرا می‌کند؛ legacy دست‌نخورده (zero double-action)
  5. parity tracker: matched/mismatched/missing + شمارنده‌ها + statusِ صادق
  6. HALT → فقط فازهای امن (ACT/effect هرگز)
$0 آفلاین؛ صفر شبکه؛ virtual clock؛ state در sandbox.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402

ENV = harness.setup("brain-core")
_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402
import brain_core as bc  # noqa: E402

_STATE = Path(str(opslib.STATE_DIR))


def _on():
    os.environ["OCTOPUS_ONE_HEARTBEAT"] = "1"


def _off():
    os.environ.pop("OCTOPUS_ONE_HEARTBEAT", None)


# ── ۱+۲: composition adapterهای واقعی، صفر ACT ──────────────────────────────────
def t_composition_real_adapters_no_act():
    _on()
    sch = bc.build_shadow_scheduler(state_dir=_STATE, clock=lambda: 1000.0, halted_fn=lambda: None)
    assert sch is not None
    phases = bc.registered_organ_phases(sch)
    assert set(phases) == {"SENSE", "RECORD", "THINK", "HEAL"}, phases
    assert "ACT" not in phases, "صفر ACT در سایه"
    names = {o.name for o in sch._organs}
    assert names == {"health", "spine-observe", "cortex-advisory", "doctor-advisory"}, names


# ── ۳: فلگ خاموش → None ─────────────────────────────────────────────────────────
def t_flag_off_no_scheduler():
    _off()
    assert bc.build_shadow_scheduler(state_dir=_STATE) is None


# ── ۴: tick اجرا می‌کند، بدونِ ACT/double-action ────────────────────────────────
def t_shadow_tick_runs_readonly():
    _on()
    sch = bc.build_shadow_scheduler(state_dir=_STATE, clock=lambda: 1000.0, halted_fn=lambda: None)
    r = sch.tick()
    assert r["beat"] == 1 and not r["degraded"]
    # SENSE/RECORD هر beat اجرا می‌شوند
    assert "health" in r["phase_order"] and "spine-observe" in r["phase_order"]
    assert r["results"]["health"]["ok"] and "organ" in str(r["results"]["health"])
    # هیچ ACT در گزارش نیست
    assert not any(o.phase == "ACT" for o in sch._organs)


# ── ۵: parity tracker ───────────────────────────────────────────────────────────
def t_parity_tracker():
    _on()
    pt = bc.ParityTracker(state_dir=_STATE)
    assert pt.compare("x", {"a": 1}, {"a": 1}) == "matched"
    assert pt.compare("x", {"a": 1}, {"a": 2}) == "mismatched"
    assert pt.compare("x", None, {"a": 1}) == "missing_old"
    assert pt.compare("x", {"a": 1}, None) == "missing_new"
    assert pt.counters["compared"] == 4 and pt.counters["matched"] == 1
    assert pt.status() in ("SHADOW-LIVE", "PARITY-GREEN")   # فلگ روشن
    _off()
    assert bc.ParityTracker(state_dir=_STATE).status() == "HARNESS"   # فلگ خاموش
    # mismatch reason بدونِ PII (فقط ساختاری)
    assert all("differs" in m["reason"] for m in pt.mismatches)


# ── ۶: HALT → فقط فازهای امن ─────────────────────────────────────────────────────
def t_halt_safe_phases_only():
    _on()
    sch = bc.build_shadow_scheduler(state_dir=_STATE, clock=lambda: 1000.0,
                                    halted_fn=lambda: "STOP-METABOLIC")
    r = sch.tick()
    assert r["halted"] == "STOP-METABOLIC"
    # SENSE/RECORD/HEAL امن؛ THINK(DECIDE-ish؟ نه، THINK امن نیست در لیستِ _SAFE) — بررسی:
    # زیرِ HALT فقط SENSE/RECORD/HEAL اجرا می‌شوند
    ran = set(r["phase_order"])
    assert "cortex-advisory" not in ran, "THINK زیرِ HALT اجرا نمی‌شود (فقط SENSE/RECORD/HEAL)"


if __name__ == "__main__":
    failed = harness.run([
        ("[۱+۲] composition adapterهای واقعی، صفر ACT", t_composition_real_adapters_no_act),
        ("[۳] فلگ خاموش → None", t_flag_off_no_scheduler),
        ("[۴] shadow tick read-only، بدونِ double-action", t_shadow_tick_runs_readonly),
        ("[۵] parity tracker + status صادق", t_parity_tracker),
        ("[۶] HALT → فقط فازهای امن", t_halt_safe_phases_only),
    ])
    sys.exit(1 if failed else 0)
