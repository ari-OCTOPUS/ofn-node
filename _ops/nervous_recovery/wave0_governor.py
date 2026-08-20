# -*- coding: utf-8 -*-
"""Wave 0 Reality Governor — machine gates. Never unlocks Wave 1 here."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import capability_immune, capability_parser, memory_continuity, receipt_v2, test_discovery

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
EFFECTORS_PY = _OPS / "effector_registry.py"
RUN_ALL = _OPS / "tests" / "run_all.py"
RECEIPTS = _OPS / "state" / "cortex" / "cost-receipts.jsonl"
MEM_LATEST = _OPS / "state" / "pulse" / "memory-read-latest.json"


class Wave0Verdict:
    PASS = "WAVE0_PASS"
    PARTIAL = "WAVE0_PARTIAL"
    BLOCKED = "WAVE0_BLOCKED"


def _sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def audit_wave0(*, receipts_path: Path | None = None,
                mem_latest: dict | None = None,
                mem_history: Path | None = None,
                run_to_task: dict[str, str] | None = None) -> dict[str, Any]:
    rec_path = Path(receipts_path or RECEIPTS)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    attr = receipt_v2.scan_jsonl(
        rec_path, run_to_task=run_to_task, since_iso=today)
    tests = test_discovery.report(run_all=RUN_ALL, tests_dir=_OPS / "tests")

    parse_ok = False
    parse_n = 0
    immune: dict[str, Any] = {"parse_ok": False, "total": 0, "counts": {}, "error": None}
    try:
        effectors = capability_parser.parse_effectors_py(EFFECTORS_PY)
        parse_ok = True
        parse_n = len(effectors)
        immune = capability_immune.inventory(
            effectors, observed_recently=False, receipt_backed=False)
    except Exception as exc:  # noqa: BLE001
        immune["error"] = f"{type(exc).__name__}: {exc}"

    latest = mem_latest
    if latest is None and MEM_LATEST.exists():
        latest = json.loads(MEM_LATEST.read_text(encoding="utf-8"))
    mem = memory_continuity.audit(latest, mem_history)

    gates = {
        "receipt_attribution": {
            "now": attr.get("ratio"),
            "threshold": 0.95,
            "pass": bool(attr.get("gate_95pct")),
            "detail": attr,
        },
        "test_registry": {
            "now": f"{tests['registered']}/{tests['discovered']}",
            "threshold": "discovered==registered",
            "pass": not tests["ci_failure"],
            "detail": {k: tests[k] for k in ("discovered", "registered", "gap",
                                             "ci_failure", "not_registered_sample")},
        },
        "memory_continuity": {
            "now": mem["consecutive_healthy"],
            "threshold": mem["threshold"],
            "pass": mem["gate_met"],
            "detail": mem,
        },
        "capability_inventory": {
            "now": parse_n,
            "threshold": "parse>0",
            "pass": parse_ok and parse_n > 0,
            "detail": {"parse_ok": parse_ok, "n": parse_n,
                       "immune_counts": immune.get("counts")},
        },
    }
    passed = sum(1 for g in gates.values() if g["pass"])
    verdict = Wave0Verdict.PASS if passed == 4 else (
        Wave0Verdict.PARTIAL if passed >= 1 else Wave0Verdict.BLOCKED
    )
    return {
        "schema": "wave0-governor/1",
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "verdict": verdict,
        "wave1_unlocked": False,
        "gates_passed": passed,
        "gates": gates,
        "github_public": "UNLOCATED",
        "git_remote": "germline E:/germline/octopus.git (not GitHub)",
        "effector_registry_sha256": _sha256_file(EFFECTORS_PY),
        "notes": [
            "WAVE0_PASS is required before readable-memory Wave 1.",
            "Rail B P0/P1 findings stay isolated (see CANDIDATE-FINDINGS).",
            "C-048..C-053 remain candidates, not CONTRADICTIONS truth.",
        ],
    }


def write_audit(dest: Path, report: dict | None = None) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    report = report if report is not None else audit_wave0()
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


if __name__ == "__main__":
    out = _ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20" / "WAVE0-GATES.json"
    p = write_audit(out)
    data = json.loads(p.read_text(encoding="utf-8"))
    print(data["verdict"], "gates", data["gates_passed"], "/4")
    print("wave1_unlocked", data["wave1_unlocked"])
