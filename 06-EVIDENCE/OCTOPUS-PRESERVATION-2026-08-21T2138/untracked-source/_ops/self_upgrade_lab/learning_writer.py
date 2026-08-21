# -*- coding: utf-8 -*-
"""Learning receipts: ledger + capability inventory + loop registry notes.
Session capsule only on milestone. Prediction mismatch lowers confidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import ROOT
from .contracts import append_jsonl, utc_now, write_json
from . import STATE_DIR

LEDGER = ROOT / "06-EVIDENCE/SESSION-HARVEST-2026-08-21/LEARNING-LEDGER.jsonl"
INVENTORY = ROOT / "_ops/state/coordination/CAPABILITY-INVENTORY-2026-08-21.json"


def write_learning(*, layer: str, hypothesis: dict, experiment: dict,
                   predicted_ok: bool, statement: str,
                   evidence_refs: list[str], confidence: float) -> str:
    lid = f"LRN-SUL-{utc_now().replace(':', '').replace('-', '')[:15]}-{layer[:3].upper()}"
    rec = {
        "learning_id": lid,
        "layer_id": layer,
        "statement": statement,
        "evidence_refs": evidence_refs,
        "confidence": round(confidence if predicted_ok else max(0.2, confidence - 0.25), 3),
        "verification_status": "tested" if experiment.get("decision") == "PROMOTE" else "observed",
        "scope": "self-upgrade-lab",
        "predicted_ok": predicted_ok,
        "mismatch": None if predicted_ok else "prediction-did-not-match-after-metrics",
        "experiment_id": experiment.get("experiment_id"),
        "hypothesis_id": hypothesis.get("hypothesis_id"),
        "recheck_at": "2026-09-21",
        "ts": utc_now(),
    }
    append_jsonl(LEDGER, rec)
    append_jsonl(STATE_DIR / "learnings.jsonl", rec)
    _touch_inventory(layer, rec)
    return lid


def _touch_inventory(layer: str, rec: dict) -> None:
    try:
        data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    caps = data.get("capabilities") or []
    key = {
        "memory": "wave1-readonly",
        "brain": "self-knowledge-ema-confidence",
        "heart": "runner-timeout-isolation",
    }.get(layer)
    for c in caps:
        if c.get("id") == key:
            ev = list(c.get("evidence") or [])
            ev.append(f"self-upgrade-lab {rec['learning_id']}")
            c["evidence"] = ev[-12:]
            break
    else:
        caps.append({
            "id": f"self-upgrade-lab-{layer}",
            "levels": {"declared": True, "implemented": True, "wired": True,
                       "callable": True, "observed": True, "tested": rec.get("predicted_ok"),
                       "verified": False},
            "evidence": [rec["learning_id"]],
            "verified_blocker": "independent verifier of promotion ladder pending",
        })
        data["capabilities"] = caps
    try:
        INVENTORY.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
