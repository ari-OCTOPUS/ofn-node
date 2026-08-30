"""Append EPI_METRIC records to a SEPARATE, independently hash-chained stream.

Guardrail: this NEVER writes to the money ledger. Off-loop, advisory, reversible,
idempotent (dedup_key).
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Optional

EPI_STREAM = "_ops/epistemics/epi-ledger.jsonl"
# Hard deny-list: the epistemics layer must never touch the financial ledger.
_MONEY_LEDGER_BASENAMES = {"ledger.jsonl"}


def _canonical(record: dict) -> str:
    return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _last_hash(path: str) -> str:
    if not os.path.exists(path):
        return "GENESIS"
    last = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                last = line.strip()
    if not last:
        return "GENESIS"
    try:
        return json.loads(last).get("hash", "GENESIS")
    except json.JSONDecodeError:
        return "GENESIS"


def _already_emitted(path: str, dedup_key: str, lookback: int = 500) -> bool:
    if not dedup_key or not os.path.exists(path):
        return False
    tail = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                tail.append(line)
    for line in tail[-lookback:]:
        try:
            if json.loads(line).get("dedup_key") == dedup_key:
                return True
        except json.JSONDecodeError:
            continue
    return False


def emit(record: dict, path: str = EPI_STREAM, dedup_key: Optional[str] = None) -> Optional[dict]:
    if os.path.basename(path) in _MONEY_LEDGER_BASENAMES:
        raise RuntimeError("epistemics must never write to the money ledger")
    if dedup_key and _already_emitted(path, dedup_key):
        return None  # idempotent: skip duplicate
    os.makedirs(os.path.dirname(path), exist_ok=True)
    prev = _last_hash(path)
    body = dict(record)
    if dedup_key:
        body["dedup_key"] = dedup_key
    body["prev_hash"] = prev
    body["hash"] = hashlib.sha256((prev + _canonical(body)).encode("utf-8")).hexdigest()
    with open(path, "a", encoding="utf-8") as f:
        f.write(_canonical(body) + "\n")
    return body
