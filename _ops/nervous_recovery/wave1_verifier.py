# -*- coding: utf-8 -*-
"""Independent Wave 1 verifier. Recomputes shadow + gates. Never unlocks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import wave0_governor, wave1_gates, wave1_readonly

_ROOT = Path(__file__).resolve().parent.parent.parent
EVID = _ROOT / "06-EVIDENCE" / "WAVE1-ENTRY-PREFLIGHT-2026-08-20"


def verify(*, evid: Path | None = None) -> dict[str, Any]:
    evid = Path(evid or EVID)
    freeze = wave1_gates.wave0_freeze_ok()
    shadow = wave1_readonly.run_shadow_sample()
    caps = wave1_gates.evaluate_capabilities(shadow)
    rollback_ok = bool(shadow.get("kill_switch_ok")) and int(shadow.get("memory_mutations") or 0) == 0
    gates = wave1_gates.entry_gates(shadow, caps, freeze, rollback_ok)
    live_w0 = wave0_governor.audit_wave0()
    checks = [
        {"name": "wave0_wave1_still_false", "ok": live_w0.get("wave1_unlocked") is False},
        {"name": "wave1_lock_or_authorized_canary",
         "ok": (
             wave1_readonly.read_lock().get("wave1_unlocked") is False
             or (wave1_readonly.read_lock().get("verifier_pass") is True
                 and wave1_readonly.read_lock().get("memory_writes") is False
                 and wave1_readonly.read_lock().get("prompt_injection") is False)
         )},
        {"name": "entry_gates_all_pass", "ok": bool(gates.get("all_pass"))},
        {"name": "shadow_n_ge_10", "ok": int(shadow.get("n") or 0) >= 10},
        {"name": "no_fabricated_task_ids", "ok": int(shadow.get("fabricated_task_ids") or 0) == 0},
        {"name": "no_memory_mutations", "ok": int(shadow.get("memory_mutations") or 0) == 0},
        {"name": "no_cross_task_leaks", "ok": not (shadow.get("cross_task_leaks") or [])},
        {"name": "kill_switch", "ok": bool(shadow.get("kill_switch_ok"))},
        {"name": "write_blocked", "ok": bool(shadow.get("write_blocked"))},
        {"name": "paid_calls_zero", "ok": shadow.get("paid_calls") == 0},
        {"name": "wave0_artifacts_unmodified",
         "ok": not freeze.get("artifact_hash_mismatches")},
    ]
    failed = [c["name"] for c in checks if not c["ok"]]
    return {
        "schema": "wave1-verifier/1",
        "confirmed": not failed,
        "failed_checks": failed,
        "checks": checks,
        "shadow_summary": {k: shadow.get(k) for k in (
            "n", "attributed", "ratio", "fabricated_task_ids", "cross_task_leaks",
            "readback_failures", "memory_mutations", "kill_switch_ok",
            "write_blocked", "paid_calls")},
        "gates_failed": gates.get("failed"),
        "wave1_unlocked": False,
        "note": "confirmed=true is a PASS of preflight gates, not a permission to write memory.",
    }


def write_report(dest: Path | None = None) -> dict[str, Any]:
    evid = EVID
    evid.mkdir(parents=True, exist_ok=True)
    dest = Path(dest or (evid / "WAVE1-VERIFIER.json"))
    rep = verify(evid=evid)
    dest.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    return rep


if __name__ == "__main__":
    r = write_report()
    print("confirmed", r["confirmed"], "failed", r["failed_checks"])
