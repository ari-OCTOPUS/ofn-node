# -*- coding: utf-8 -*-
"""Merge Wave 0 artifacts into the Reality Ledger. Append-only; no CONTRADICTIONS writes."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .reality_ledger import RealityLedger

_OPS = Path(__file__).resolve().parent.parent
_ROOT = _OPS.parent
EVID = _ROOT / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20"
LEDGER = EVID / "reality-ledger.jsonl"


def _sha256_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _event(fid: str, *, ref: str, digest: str | None, notes: str,
           status: str = "confirmed", severity: str = "INFO",
           kind: str = "finding", source: str = "nervous-recovery",
           confidence: float = 0.9) -> dict[str, Any]:
    return {
        "kind": kind,
        "finding_id": fid,
        "status": status,
        "severity": severity,
        "source_agent": source,
        "confidence": confidence,
        "notes": notes,
        "evidence": [{
            "type": "file",
            "ref": ref,
            "hash": digest or "UNLOCATED",
        }],
    }


def merge_wave0(*, ledger_path: Path | None = None,
                evid: Path | None = None) -> dict[str, Any]:
    evid = Path(evid or EVID)
    lg = RealityLedger(Path(ledger_path or LEDGER))
    artifacts = [
        ("REALITY_SNAPSHOT", evid / "WAVE0-GATES.json",
         "Governor snapshot of four Wave 0 gates."),
        ("TEST_REGISTRY", evid / "TEST-CLASSIFY-FULL.json",
         "Classification of previously unregistered tests."),
        ("RECEIPT_ATTRIBUTION_AUDIT", evid / "SHADOW-WINDOW.json",
         "Shadow hygiene of today's cost-receipts window."),
        ("CAPABILITY_INVENTORY", evid / "CAPABILITY-INVENTORY.json",
         "AST parse + immune cards for 10 EFFECTORS."),
        ("MEMORY_READ_GATE", evid / "memory-continuity.jsonl",
         "Observed memory-read ticks; streak not a sum."),
        ("NERVOUS_RECOVERY", evid / "README.md",
         "Nervous-recovery evidence pack index."),
        ("DEEP_SCAN", _ROOT / "06-EVIDENCE" / "DEEP-SCAN-DOCTOR-SELFAWARENESS-BRAINS-2026-08-20.md",
         "Deep-scan report 2026-08-20 — candidate seams only."),
        ("SEAM_HUNT", _ROOT / "06-EVIDENCE" / "SEAM-HUNT-MINUTELY" / "DISCOVERIES-2026-08-20.md",
         "Seam-hunt discoveries 2026-08-20 — not CONTRADICTIONS truth."),
        ("CANARY_CORTEX", evid / "CANARY-POST-CORTEX.json",
         "Cortex canary post-check; daemon/live unchanged."),
        ("STAGE_A", evid / "STAGE-A.md", "Stage A baseline vs owner table."),
        ("STAGE_B", evid / "STAGE-B.md", "Stage B attribution plumbing."),
        ("STAGE_C", evid / "STAGE-C.md", "Stage C cortex canary."),
    ]
    results: list[dict[str, Any]] = []
    for fid, path, note in artifacts:
        digest = _sha256_file(path)
        rel = str(path.relative_to(_ROOT)) if path.is_relative_to(_ROOT) else str(path)
        ev = _event(fid, ref=rel.replace("\\", "/"), digest=digest, notes=note,
                    kind="verification", status="confirmed")
        results.append({"finding_id": fid, **lg.append(ev)})

    # Conflicts kept; nothing deleted. C-048..C-053 stay candidates.
    conflicts = [
        _event(
            "CONFLICT-ATTR-DENOMINATOR",
            ref="06-EVIDENCE/NERVOUS-RECOVERY-2026-08-20/WAVE0-GATES.json",
            digest=_sha256_file(evid / "WAVE0-GATES.json"),
            notes=(
                "today-full attribution 0.3423 (51/149, 98 pre-schema) vs "
                "schema-present 1.0 (51/51). Pre-schema rows not rewritten. "
                "C-053 remains candidate (WAVE0-ATTR)."
            ),
            status="candidate",
            severity="MEDIUM",
            kind="finding",
            confidence=1.0,
        ),
        _event(
            "CONFLICT-C048-NUMBER",
            ref="06-EVIDENCE/SEAM-HUNT-MINUTELY/DISCOVERIES-2026-08-20.md",
            digest=_sha256_file(
                _ROOT / "06-EVIDENCE" / "SEAM-HUNT-MINUTELY" / "DISCOVERIES-2026-08-20.md"),
            notes=(
                "C-048 number collision: S-B01 fugu quota vs S-A14 duplicate "
                "cognition-note numbers. Neither entered CONTRADICTIONS.md."
            ),
            status="candidate",
            severity="MEDIUM",
            kind="finding",
            confidence=0.9,
        ),
        _event(
            "CONFLICT-BCM-CONSUMER",
            ref="_ops/effector_registry.py",
            digest=_sha256_file(_OPS / "effector_registry.py"),
            notes=(
                "EFFECTORS marks bcm.weights_bidirectional display-only; "
                "DEEP-SEAMS-2026-08-16 claims production readers. Both kept."
            ),
            status="candidate",
            severity="LOW",
            kind="finding",
            confidence=0.7,
        ),
    ]
    for ev in conflicts:
        results.append({"finding_id": ev["finding_id"], **lg.append(ev)})

    candidates = ["S-B01", "S-B02", "S-B06", "S-D01", "S-B05", "WAVE0-ATTR"]
    return {
        "schema": "wave0-artifact-merge/1",
        "ledger": str(lg.path),
        "appended_or_deduped": results,
        "candidates_untouched": candidates,
        "contradictions_md_writes": 0,
        "wave1_unlocked": False,
    }
