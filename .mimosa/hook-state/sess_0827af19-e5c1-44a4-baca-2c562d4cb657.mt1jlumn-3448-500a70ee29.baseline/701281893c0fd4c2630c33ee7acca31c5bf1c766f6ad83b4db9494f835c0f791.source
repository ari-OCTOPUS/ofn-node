# -*- coding: utf-8 -*-
"""Wave 1 preflight closeout: freeze Wave 0, shadow, verify, optional canary.

Never writes memory.db or cost-receipts.jsonl. Paid calls = 0.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from . import wave1_gates, wave1_readonly, wave1_verifier

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
EVID = _ROOT / "06-EVIDENCE" / "WAVE1-ENTRY-PREFLIGHT-2026-08-20"
LOCK = _OPS / "state" / "wave1" / "lock.json"


def _sha(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        path.write_text(obj, encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def production_fingerprints() -> dict:
    paths = {
        "cost_receipts": _OPS / "state" / "cortex" / "cost-receipts.jsonl",
        "memory_db": _OPS / "state" / "memory" / "memory.db",
        "pulse_latest": _OPS / "state" / "pulse" / "memory-read-latest.json",
        "wave0_gates": _ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20" / "WAVE0-GATES.json",
    }
    return {k: {"path": str(p), "sha256": _sha(p), "exists": p.is_file()}
            for k, p in paths.items()}


def run(*, activate_canary: bool = True) -> dict:
    evid = EVID
    evid.mkdir(parents=True, exist_ok=True)
    wave1_readonly.freeze_lock_closed(LOCK)
    before = production_fingerprints()
    freeze = wave1_gates.wave0_freeze_ok()
    _write(evid / "WAVE0-FREEZE.json", {
        "schema": "wave0-freeze/1",
        "commit": "9bc506f",
        "ts": _utc(),
        "freeze": freeze,
        "production_before": before,
        "note": "Wave 0 artifacts must remain bit-identical.",
    })

    shadow = wave1_readonly.run_shadow_sample()
    # Persist receipts beside evidence, never into cost-receipts.jsonl.
    rec_path = evid / "wave1-shadow-receipts.jsonl"
    with rec_path.open("w", encoding="utf-8") as f:
        for row in shadow.get("receipts") or []:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    shadow_pub = {k: v for k, v in shadow.items() if k != "receipts"}
    shadow_pub["receipts_path"] = str(rec_path)
    _write(evid / "WAVE1-SHADOW-RESULTS.json", shadow_pub)

    caps = wave1_gates.evaluate_capabilities(shadow)
    _write(evid / "WAVE1-CAPABILITY-GATE.json", caps)
    rollback_ok = bool(shadow.get("kill_switch_ok")) and int(shadow.get("memory_mutations") or 0) == 0
    gates = wave1_gates.entry_gates(shadow, caps, freeze, rollback_ok)
    _write(evid / "WAVE1-ENTRY-GATES.json", gates)

    verifier = wave1_verifier.write_report(evid / "WAVE1-VERIFIER.json")
    after_shadow = production_fingerprints()
    mutated_prod = [k for k in before
                    if before[k].get("sha256") != after_shadow[k].get("sha256")]

    canary = None
    activated = False
    if (activate_canary and verifier.get("confirmed") and gates.get("all_pass")
            and not mutated_prod):
        _write(evid / "WAVE1_PASS_CANDIDATE.json", {
            "schema": "wave1-pass-candidate/1",
            "ts": _utc(),
            "status": "WAVE1_PASS_CANDIDATE",
            "wave0_governor_wave1_unlocked": False,
            "canary_scope": "sidecar-fixture-only",
            "prompt_injection": False,
            "memory_writes": False,
        })
        # Limited canary: re-run shadow under the authorized API. No process restart.
        canary_shadow = wave1_readonly.run_shadow_sample()
        fab = canary_shadow.get("fabricated_task_ids")
        canary_ok = (
            canary_shadow.get("memory_mutations") == 0
            and not (canary_shadow.get("cross_task_leaks") or [])
            and canary_shadow.get("kill_switch_ok") is True
            and fab == 0
        )
        after_canary = production_fingerprints()
        mutated_canary = [k for k in before
                          if before[k].get("sha256") != after_canary[k].get("sha256")]
        canary = {
            "schema": "wave1-canary/1",
            "ok": canary_ok and not mutated_canary,
            "production_hash_delta": mutated_canary,
            "shadow_n": canary_shadow.get("n"),
            "mutations": canary_shadow.get("memory_mutations"),
            "leaks": canary_shadow.get("cross_task_leaks"),
            "kill_switch_ok": canary_shadow.get("kill_switch_ok"),
            "restarts": 0,
            "paid_calls": 0,
        }
        _write(evid / "WAVE1-CANARY.json", canary)
        if canary["ok"]:
            lock = {
                "schema": "wave1-lock/1",
                "wave1_unlocked": True,
                "verifier_pass": True,
                "updated": _utc(),
                "activation": "canary-sidecar",
                "prompt_injection": False,
                "memory_writes": False,
                "organism_hook": False,
                "note": (
                    "Wave 1 read-only API authorized for callers that pass task_id. "
                    "wave0_governor.wave1_unlocked remains false. No prompt injection."
                ),
            }
            _write(LOCK, lock)
            _write(evid / "WAVE1-LOCK-COPY.json", lock)
            activated = True

    after = production_fingerprints()
    out = {
        "schema": "wave1-closeout/1",
        "ts": _utc(),
        "verifier_confirmed": bool(verifier.get("confirmed")),
        "entry_gates_all_pass": bool(gates.get("all_pass")),
        "gates_failed": gates.get("failed"),
        "production_mutations": [k for k in before
                                 if before[k].get("sha256") != after[k].get("sha256")],
        "canary": canary,
        "wave1_api_unlocked": activated,
        "wave0_governor_wave1_unlocked": False,
        "paid_calls": 0,
        "restarts": 0,
    }
    _write(evid / "WAVE1-CLOSEOUT.json", out)
    return out


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
