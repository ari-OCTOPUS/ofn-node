# -*- coding: utf-8 -*-
"""Capability Immune System — declared ≠ alive."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

TRUTH = (
    "VERIFIED",
    "DEGRADED",
    "DECLARED_UNOBSERVED",
    "DORMANT",
    "BLOCKED",
    "UNKNOWN",
)

_OPS = Path(__file__).resolve().parent.parent


def card(name: str, spec: dict[str, Any], *,
         observed_recently: bool | None = None,
         receipt_backed: bool | None = None,
         tested: str | bool | None = None) -> dict[str, Any]:
    actuator = spec.get("actuator")
    callable_ = actuator not in (None, "", False)
    st = str(spec.get("status") or "")
    tested_ok = tested is True

    if (receipt_backed is True and observed_recently is True and callable_
            and tested_ok):
        truth = "VERIFIED"
    elif st == "dead-output" or (not callable_ and receipt_backed is not True and bool(st)):
        # Proven inactive / unreachable call path — not merely "no receipt".
        truth = "DORMANT"
    elif receipt_backed is True and callable_ and (
            observed_recently is False or not tested_ok):
        truth = "DEGRADED"
    elif receipt_backed is not True and callable_:
        # Declared + callable, but no attributable receipt yet.
        truth = "DECLARED_UNOBSERVED"
    elif observed_recently is None and receipt_backed is None and not st:
        truth = "UNKNOWN"
    else:
        truth = "UNKNOWN"

    return {
        "capability": name,
        "declared": True,
        "callable": callable_,
        "observed_recently": observed_recently if observed_recently is not None else "UNKNOWN",
        "tested": tested if tested is not None else "UNKNOWN",
        "receipt_backed": bool(receipt_backed),
        "dependency_state": spec.get("gate") or "none",
        "registry_status": st or "UNKNOWN",
        "truth_status": truth,
        "propose_only": spec.get("propose_only"),
        "note": (
            "VERIFIED requires declaration + callable path + recent receipt + test. "
            "DECLARED_UNOBSERVED = missing attributable receipt, not proof the "
            "capability is absent. DORMANT = call path inactive/unreachable."
        ),
    }


def inventory(effectors: dict[str, dict], **flags) -> dict[str, Any]:
    cards = [card(k, v, **flags) for k, v in effectors.items()]
    counts: dict[str, int] = {t: 0 for t in TRUTH}
    for c in cards:
        counts[str(c["truth_status"])] = counts.get(str(c["truth_status"]), 0) + 1
    return {
        "schema": "capability-immune/2",
        "total": len(cards),
        "parse_ok": True,
        "counts": counts,
        "cards": cards,
    }


def _sha256_file(p: Path) -> str | None:
    if not p.is_file():
        return None
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _produced_source(spec: dict[str, Any], ops: Path) -> Path | None:
    raw = str(spec.get("produced_by") or "")
    token = raw.split("→")[0].split("(")[0].split("+")[0].strip()
    if not token:
        return None
    token = token.replace("\\", "/")
    if token.startswith("_ops/"):
        return ops / token[len("_ops/"):]
    if "/" in token:
        cand = ops / token
        if cand.exists():
            return cand
        cand = ops.parent / token
        if cand.exists():
            return cand
    return None


def _receipt_ids_for(name: str, receipts_path: Path, *, limit: int = 200000) -> list[str]:
    if not receipts_path.is_file():
        return []
    hits: list[str] = []
    with receipts_path.open(encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            raw = line.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except ValueError:
                continue
            cap = str(row.get("capability_id") or row.get("capability") or "")
            if cap == name:
                rid = str(row.get("receipt_id") or row.get("trace_id") or "")
                if rid:
                    hits.append(rid)
    return hits


def evaluate_declared(effectors: dict[str, dict], *,
                      receipts_path: Path | None = None,
                      tests_dir: Path | None = None,
                      ops: Path | None = None) -> dict[str, Any]:
    """Per-capability cards with evidence hashes. Never infers VERIFIED."""
    ops = Path(ops or _OPS)
    receipts_path = Path(receipts_path or (ops / "state" / "cortex" / "cost-receipts.jsonl"))
    tests_dir = Path(tests_dir or (ops / "tests"))
    registry_hash = _sha256_file(ops / "effector_registry.py")
    cards: list[dict[str, Any]] = []
    for name, spec in effectors.items():
        receipt_ids = _receipt_ids_for(name, receipts_path)
        test_name = f"test_{name.replace('.', '_')}.py"
        tested = (tests_dir / test_name).is_file()
        src = _produced_source(spec, ops)
        src_hash = _sha256_file(src) if src else None
        c = card(
            name, spec,
            observed_recently=bool(receipt_ids),
            receipt_backed=bool(receipt_ids),
            tested=True if tested else False,
        )
        c["evidence"] = [
            {"type": "file", "ref": "_ops/effector_registry.py", "hash": registry_hash},
            {"type": "file", "ref": str(src) if src else "UNLOCATED",
             "hash": src_hash or "UNLOCATED"},
        ]
        c["receipt_ids_sample"] = receipt_ids[-3:]
        c["dedicated_test"] = test_name if tested else None
        cards.append(c)
    counts: dict[str, int] = {t: 0 for t in TRUTH}
    for c in cards:
        counts[str(c["truth_status"])] = counts.get(str(c["truth_status"]), 0) + 1
    return {
        "schema": "capability-immune/3",
        "total": len(cards),
        "parse_ok": True,
        "counts": counts,
        "cards": cards,
        "registry_sha256": registry_hash,
        "wave1_unlocked": False,
        "note": "Absence of a cost-receipt is not proof of DORMANT.",
    }
