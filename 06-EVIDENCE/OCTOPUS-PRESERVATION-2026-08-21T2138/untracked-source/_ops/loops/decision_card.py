# -*- coding: utf-8 -*-
"""Decision cards with expiry. Silence applies the safe default, never no-op-forever."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


def make_card(
    *,
    loop_id: str,
    question: str,
    options: list[str],
    safe_default: str,
    ttl_s: float,
    now: float | None = None,
) -> dict[str, Any]:
    t = float(now if now is not None else time.time())
    if safe_default not in options:
        raise ValueError("safe_default must be one of options")
    body = f"{loop_id}:{question}:{t}"
    card_id = "crd_" + hashlib.sha256(body.encode()).hexdigest()[:12]
    nonce = hashlib.sha256(f"{card_id}:nonce:{t}".encode()).hexdigest()[:16]
    return {
        "schema": "decision-card/1",
        "card_id": card_id,
        "nonce": nonce,
        "loop_id": loop_id,
        "question": question,
        "options": list(options),
        "safe_default": safe_default,
        "created_at": t,
        "expires_at": t + float(ttl_s),
        "status": "open",
        "applied": None,
    }


def apply_if_expired(card: dict[str, Any], now: float | None = None) -> dict[str, Any]:
    t = float(now if now is not None else time.time())
    out = dict(card)
    if out.get("status") != "open":
        return out
    if t < float(out.get("expires_at") or 0):
        return out
    out["status"] = "expired_applied"
    out["applied"] = out.get("safe_default")
    out["applied_at"] = t
    return out


def resolve(card: dict[str, Any], choice: str, nonce: str,
            now: float | None = None) -> dict[str, Any]:
    t = float(now if now is not None else time.time())
    out = dict(card)
    if nonce != out.get("nonce"):
        out["status"] = "rejected_stale_nonce"
        return out
    if t >= float(out.get("expires_at") or 0):
        return apply_if_expired(out, now=t)
    if choice not in (out.get("options") or []):
        out["status"] = "rejected_unknown_option"
        return out
    out["status"] = "resolved"
    out["applied"] = choice
    out["applied_at"] = t
    return out


def write_ledger(path: Path, card: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(card, ensure_ascii=False) + "\n")
