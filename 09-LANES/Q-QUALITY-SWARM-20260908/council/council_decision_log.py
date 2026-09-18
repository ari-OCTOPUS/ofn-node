"""Append-only council decision log for the next 50 four-model votes.

Does not compute correlation. Records votes so a later pass can.
No network. No secrets.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODELS = ("GLM", "DeepSeek", "Ollama", "Fugu")
TARGET_N = 50
SCHEMA = "council.decision.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_record(rec: dict[str, Any]) -> None:
    if rec.get("schema") != SCHEMA:
        raise ValueError("schema")
    if not rec.get("decision_id"):
        raise ValueError("decision_id")
    votes = rec.get("votes")
    if not isinstance(votes, dict):
        raise ValueError("votes")
    for m in MODELS:
        if m not in votes:
            raise ValueError(f"missing-vote:{m}")
        if votes[m] not in ("agree", "dissent", "abstain", "error", "absent"):
            raise ValueError(f"vote-enum:{m}")
    outcome = rec.get("outcome")
    if outcome not in ("resolved", "unresolved", "owner"):
        raise ValueError("outcome")


def append_decision(log_path: Path, rec: dict[str, Any]) -> dict:
    rec = dict(rec)
    rec.setdefault("schema", SCHEMA)
    rec.setdefault("ts", _utc_now())
    validate_record(rec)
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = count(path)
    if n >= TARGET_N:
        raise ValueError("target-n-reached")
    rec["seq"] = n + 1
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
    return rec


def count(log_path: Path) -> int:
    path = Path(log_path)
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def remaining(log_path: Path) -> int:
    return max(0, TARGET_N - count(log_path))
