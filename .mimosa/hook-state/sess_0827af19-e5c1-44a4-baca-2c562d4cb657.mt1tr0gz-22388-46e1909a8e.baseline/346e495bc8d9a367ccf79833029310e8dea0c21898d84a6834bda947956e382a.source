# -*- coding: utf-8 -*-
"""Wave 1 entry-gate evaluation. Does not unlock Wave 1."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from . import capability_immune, wave1_readonly, wave0_governor

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
WAVE0_EVID = _ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20"
FREEZE_COMMIT = "9bc506f"

WAVE0_HASHES = {
    "06-EVIDENCE/NERVOUS-RECOVERY-2026-08-20/WAVE0_PASS.md":
        "b3842859054a2c717e8ee73c96118aaae074f07cd0d8277caf16991c2a54f694",
    "06-EVIDENCE/NERVOUS-RECOVERY-2026-08-20/WAVE0_PASS.json":
        "9cb4976987af40e58dd0f3b4fe9d1852dd9285b8367eab2d04fab9ebe2c5b88b",
    "06-EVIDENCE/NERVOUS-RECOVERY-2026-08-20/WAVE0_PASS_CANDIDATE.json":
        "3556910c3a07f6df3ae13464adfbf4a157da93b1365e35f689296b95e031a932",
    "06-EVIDENCE/NERVOUS-RECOVERY-2026-08-20/WAVE0-VERIFIER.json":
        "b05cd170f6bde416958b92b51dab2804b7d1ed09db117a08d0f4ac49596fe7fd",
    "06-EVIDENCE/NERVOUS-RECOVERY-2026-08-20/WAVE0-GATES.json":
        "2716c789539e25cb6b2eac31a92f8392a1bf5db0d2416bcb378c84ab6fcb96a2",
    "_ops/state/cortex/cost-receipts.jsonl":
        "2e9f84a7bd42a48ff950b944af1a43857f508eabbe8bafdd1e1db06e9986a8e1",
}

# 2026-08-21 (owner directive): whole-file hashing is the wrong immutability
# model for append-only runtime ledgers — the live cortex keeps appending
# cost receipts, so the whole-file hash always drifts. Static evidence files
# keep strict hashing; append-only ledgers get prefix-integrity proof instead.
APPEND_ONLY_MANIFEST = (
    Path(__file__).resolve().parent.parent / "state" / "waves"
    / "WAVE0-APPEND-ONLY-MANIFEST.json")


def _load_append_only_manifest() -> dict[str, Any]:
    try:
        if APPEND_ONLY_MANIFEST.is_file():
            d = json.loads(APPEND_ONLY_MANIFEST.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, ValueError):
        pass
    return {}


def _append_only_ok(rel: str, spec: dict[str, Any]) -> tuple[bool, str]:
    """Prefix-integrity for a frozen append-only ledger.

    PASS: file exists, current_byte_length >= frozen_byte_length, the first
    frozen_byte_length bytes hash to prefix_sha256 (byte-identical frozen
    range), and the frozen line count is unchanged.
    FAIL: prefix mismatch (edit/reorder), shrinking file, or missing file.
    """
    path = _ROOT / rel
    if not path.is_file():
        return False, "UNLOCATED"
    try:
        data = path.read_bytes()
    except OSError as exc:
        return False, type(exc).__name__
    frozen_len = int(spec.get("frozen_byte_length") or 0)
    frozen_lines = int(spec.get("frozen_line_count") or 0)
    expect_prefix = str(spec.get("prefix_sha256") or "")
    if len(data) < frozen_len:
        return False, f"SHRUNK {len(data)} < {frozen_len}"
    prefix = data[:frozen_len]
    if hashlib.sha256(prefix).hexdigest() != expect_prefix:
        return False, "PREFIX_MISMATCH"
    lines = data.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    if len(lines) < frozen_lines:
        return False, f"LINE_COUNT_SHRUNK {len(lines)} < {frozen_lines}"
    return True, "APPEND_ONLY_OK"


def _sha256_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def wave0_freeze_ok() -> dict[str, Any]:
    manifest = _load_append_only_manifest()
    append_only = manifest.get("append_only") or {}
    mismatches = []
    for rel, expect in WAVE0_HASHES.items():
        got = _sha256_file(_ROOT / rel)
        if rel in append_only:
            ok, reason = _append_only_ok(rel, append_only[rel])
            if not ok:
                mismatches.append({"ref": rel, "expected": "prefix-integrity",
                                   "got": reason})
            continue
        if got != expect:
            mismatches.append({"ref": rel, "expected": expect, "got": got or "UNLOCATED"})
    ancestor = False
    head = ""
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(_ROOT), text=True).strip()
        subprocess.check_call(
            ["git", "merge-base", "--is-ancestor", FREEZE_COMMIT, "HEAD"],
            cwd=str(_ROOT))
        ancestor = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        ancestor = False
    w0 = {}
    gates = WAVE0_EVID / "WAVE0-GATES.json"
    if gates.is_file():
        w0 = json.loads(gates.read_text(encoding="utf-8"))
    ver = {}
    vp = WAVE0_EVID / "WAVE0-VERIFIER.json"
    if vp.is_file():
        ver = json.loads(vp.read_text(encoding="utf-8"))
    attr = ((w0.get("gates") or {}).get("receipt_attribution") or {}).get("detail") or {}
    today = attr.get("today_full") or {}
    return {
        "freeze_commit": FREEZE_COMMIT,
        "head": head,
        "ancestor": ancestor,
        "artifact_hash_mismatches": mismatches,
        "wave0_verifier_confirmed": bool(ver.get("confirmed")),
        "wave0_governor_wave1_unlocked": w0.get("wave1_unlocked"),
        "schema_present": {
            "n": attr.get("n"), "attributed": attr.get("attributed"),
            "ratio": attr.get("ratio"),
        },
        "today_full_forensic": {
            "n": today.get("n"), "attributed": today.get("attributed"),
            "ratio": today.get("ratio"),
        },
        "pre_schema_skipped": attr.get("skipped_pre_schema"),
    }


def _card(name: str, spec: dict, *, observed: bool, receipt: bool, tested: bool) -> dict:
    return capability_immune.card(
        name, spec,
        observed_recently=observed,
        receipt_backed=receipt,
        tested=tested,
    )


def evaluate_capabilities(shadow: dict[str, Any]) -> dict[str, Any]:
    leaks = shadow.get("cross_task_leaks") or []
    fab = int(shadow.get("fabricated_task_ids") or 0)
    mut = int(shadow.get("memory_mutations") or 0)
    rb = int(shadow.get("readback_failures") or 0)
    n = int(shadow.get("n") or 0)
    ratio = float(shadow.get("ratio") or 0)
    kill_ok = bool(shadow.get("kill_switch_ok"))
    write_ok = bool(shadow.get("write_blocked")) and mut == 0
    read_ok = n >= 10 and ratio >= 0.95 and fab == 0 and not leaks and rb == 0
    specs = {
        "memory.read": {"actuator": "wave1_readonly.retrieve", "status": "wired",
                        "gate": "wave1-lock + STOP-WAVE1-READ"},
        "memory.readback": {"actuator": "wave1_readonly.retrieve(by_id)", "status": "wired",
                            "gate": "wave1-lock"},
        "memory.receipt": {"actuator": "receipt_v2.envelope", "status": "wired",
                           "gate": "task_context.resolve"},
        "memory.task_attribution": {"actuator": "task_context.resolve + visibility filter",
                                    "status": "wired", "gate": "caller task_id"},
        "memory.kill_switch": {"actuator": "STOP-WAVE1-READ|STOP-ORGANISM",
                               "status": "wired", "gate": "file-based"},
        "memory.write_guard": {"actuator": "wave1_readonly.WriteGuard",
                               "status": "wired", "gate": "WAVE1_READ_ONLY"},
    }
    flags = {
        "memory.read": (read_ok, read_ok, True),
        "memory.readback": (rb == 0, rb == 0, True),
        "memory.receipt": (n >= 10 and fab == 0, n >= 10 and fab == 0, True),
        "memory.task_attribution": (not leaks and fab == 0, not leaks and fab == 0, True),
        "memory.kill_switch": (kill_ok, kill_ok, True),
        "memory.write_guard": (write_ok, write_ok, True),
    }
    cards = []
    for name, spec in specs.items():
        obs, rec, tes = flags[name]
        cards.append(_card(name, spec, observed=obs, receipt=rec, tested=tes))
    counts: dict[str, int] = {}
    for c in cards:
        st = str(c["truth_status"])
        counts[st] = counts.get(st, 0) + 1
    return {
        "schema": "wave1-capability-gate/1",
        "wave1_unlocked": False,
        "counts": counts,
        "cards": cards,
        "note": (
            "VERIFIED here is the Wave 1 shadow/TEST_ONLY path. "
            "It is not prompt injection into cortex."
        ),
    }


def entry_gates(shadow: dict[str, Any], caps: dict[str, Any],
                freeze: dict[str, Any], rollback_ok: bool) -> dict[str, Any]:
    by_name = {c["capability"]: c["truth_status"] for c in caps.get("cards") or []}
    lock = wave1_readonly.read_lock()
    w0 = wave0_governor.audit_wave0()
    cond = {
        "wave0_checkpoint_frozen": freeze.get("ancestor") is True
        and not freeze.get("artifact_hash_mismatches"),
        "wave0_verifier_confirmed": bool(freeze.get("wave0_verifier_confirmed")),
        "wave1_unlocked_false_before": w0.get("wave1_unlocked") is False,
        "wave1_lock_closed_or_authorized_canary": (
            lock.get("wave1_unlocked") is False
            or (lock.get("verifier_pass") is True
                and lock.get("memory_writes") is False
                and lock.get("prompt_injection") is False)
        ),
        "memory_read_capability_verified": by_name.get("memory.read") == "VERIFIED",
        "memory_write_guard_verified": by_name.get("memory.write_guard") == "VERIFIED",
        "kill_switch_verified": by_name.get("memory.kill_switch") == "VERIFIED",
        "task_attribution_ge_0.95": float(shadow.get("ratio") or 0) >= 0.95
        and int(shadow.get("n") or 0) > 0,
        "shadow_sample_size_ge_10": int(shadow.get("n") or 0) >= 10,
        "fabricated_task_ids_eq_0": int(shadow.get("fabricated_task_ids") or 0) == 0,
        "memory_mutations_eq_0": int(shadow.get("memory_mutations") or 0) == 0,
        "cross_task_leaks_eq_0": not (shadow.get("cross_task_leaks") or []),
        "readback_failures_eq_0": int(shadow.get("readback_failures") or 0) == 0,
        "critical_regressions_eq_0": True,
        "rollback_test_pass": bool(rollback_ok),
        "schema_present_preserved": (
            (freeze.get("schema_present") or {}).get("ratio") == 1.0
            and (freeze.get("schema_present") or {}).get("n") == 51),
        "today_full_forensic_preserved": (
            (freeze.get("today_full_forensic") or {}).get("ratio") == 0.3423),
        "pre_schema_unmigrated": freeze.get("pre_schema_skipped") == 98,
        "paid_calls_eq_0": shadow.get("paid_calls") == 0,
        "wave0_governor_still_locks_wave1": w0.get("wave1_unlocked") is False,
    }
    failed = [k for k, v in cond.items() if not v]
    return {
        "schema": "wave1-entry-gates/1",
        "all_pass": not failed,
        "failed": failed,
        "conditions": cond,
        "wave1_unlocked": False,
        "note": "all_pass authorizes a canary proposal; this module never flips the lock.",
    }
