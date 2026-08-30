#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Typed handshake Evidence Envelope — 12 groups, stdlib-only, $0.

WAVE0_OBSERVE_ONLY. This module does not raise autonomy, touch TCB, or
clear GITWRITE-FAILED. Verifier sees the artifact, not the author's chain.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "octopus-handshake-envelope/1"
SENDER_LAPTOP = "agent://octopus/laptop-brain/main"
RECEIVER_SENSORIUM = "agent://octopus/sensorium-board/main"
RECEIVER_FEET = "agent://octopus/feet-board/main"
# Additive: .180 continuity board. Do not replace sensorium/feet ids.
RECEIVER_CONTINUITY = "agent://octopus/continuity-board/main"
OWNER = "Armin"
MAX_RETRIES = 3

REQUIRED_TOP = (
    "schema", "identity", "relation", "goal", "scope", "status",
    "inputs", "decisions", "artifacts", "evidence", "authority",
    "sensitivity", "uncertainty", "escalation",
)
REQUIRED_IDENTITY = (
    "handoff_id", "task_id", "sender", "receiver", "initiating_owner",
)
REQUIRED_EVIDENCE = ("claim", "raw", "reproduction_command")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_envelope(env: dict[str, Any]) -> list[str]:
    """Return error codes (empty = valid). Never raises."""
    errors: list[str] = []
    if not isinstance(env, dict):
        return ["not-a-dict"]
    if env.get("schema") != SCHEMA:
        errors.append("bad-schema")
    for k in REQUIRED_TOP:
        if k not in env:
            errors.append(f"missing-group:{k}")
    ident = env.get("identity") if isinstance(env.get("identity"), dict) else {}
    for k in REQUIRED_IDENTITY:
        if not str(ident.get(k) or "").strip():
            errors.append(f"missing-identity:{k}")
    ev = env.get("evidence") if isinstance(env.get("evidence"), dict) else {}
    for k in REQUIRED_EVIDENCE:
        if k not in ev:
            errors.append(f"missing-evidence:{k}")
    claim = str(ev.get("claim") or "").strip()
    raw = ev.get("raw")
    repro = str(ev.get("reproduction_command") or "").strip()
    if claim and not repro:
        errors.append("claim-without-reproduction-command")
    if claim and (not isinstance(raw, list) or len(raw) == 0):
        errors.append("claim-without-raw-evidence")
    if isinstance(raw, list):
        for i, row in enumerate(raw):
            if not isinstance(row, dict):
                errors.append(f"raw-{i}-not-dict")
                continue
            if not str(row.get("command") or "").strip():
                errors.append(f"raw-{i}-missing-command")
            if "exit" not in row:
                errors.append(f"raw-{i}-missing-exit")
            has_body = bool(str(row.get("stdout") or "")) or bool(str(row.get("stderr") or ""))
            if not has_body and row.get("exit") not in (0, "0"):
                # failed command with empty body is still evidence if exit is set
                pass
            if not has_body and row.get("exit") is None:
                errors.append(f"raw-{i}-empty-body")
    auth = env.get("authority") if isinstance(env.get("authority"), dict) else {}
    if auth.get("may_authorize") is True:
        errors.append("may_authorize-must-be-false-in-wave0")
    if auth.get("autonomy_delta") not in (0, 0.0, None):
        errors.append("autonomy-delta-must-be-zero")
    esc = env.get("escalation") if isinstance(env.get("escalation"), dict) else {}
    try:
        mx = int(esc.get("max_retries", MAX_RETRIES))
    except (TypeError, ValueError):
        mx = -1
    if mx < 1 or mx > 5:
        errors.append("max_retries-out-of-range")
    return errors


def make_envelope(*, receiver: str, task_id: str, claim: str,
                  raw: list[dict], reproduction_command: str,
                  goal: str, decisions: list[dict], artifacts: list[dict],
                  uncertainty_notes: list[str],
                  escalation_on_fail: str,
                  status: dict | None = None,
                  inputs: list | None = None,
                  retry_count: int = 0,
                  changelog_seq: int = 1,
                  extra: dict | None = None) -> dict[str, Any]:
    env = {
        "schema": SCHEMA,
        "identity": {
            "handoff_id": new_id("ho"),
            "task_id": task_id,
            "sender": SENDER_LAPTOP,
            "receiver": receiver,
            "initiating_owner": OWNER,
            "host": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "",
        },
        "relation": {
            "role": "source-of-truth",
            "sees": "peer-artifacts-only",
            "does_not_see": "peer-reasoning-chain",
            "modality_shift": True,
        },
        "goal": {
            "one_sentence": goal,
            "cycle": task_id,
        },
        "scope": {
            "vault": r"F:\backup",
            "may_exec_on_feet": False,
            "may_edit_tcb": False,
            "may_clear_gitwrite_flag": False,
        },
        "status": status or {
            "operational": "WAVE0_OBSERVE_ONLY",
            "authority_level": "L2-armed-propose-only",
            "gap_001": "open",
        },
        "inputs": list(inputs or []),
        "decisions": list(decisions),
        "artifacts": list(artifacts),
        "evidence": {
            "claim": claim,
            "raw": list(raw),
            "reproduction_command": reproduction_command,
        },
        "authority": {
            "may_authorize": False,
            "autonomy_delta": 0,
            "external_effect": False,
            "propose_only": True,
        },
        "sensitivity": {
            "secrets_in_envelope": False,
            "classification": "ops-internal",
        },
        "uncertainty": {
            "notes": list(uncertainty_notes),
            "tz_note": "Sydney in August is AEST UTC+10; megaprompt said UTC+11 — using OS local offset",
        },
        "escalation": {
            "on_repro_fail": escalation_on_fail,
            "max_retries": MAX_RETRIES,
            "retry_count": int(retry_count),
            "after_max": "owner",
        },
        "changelog_seq": int(changelog_seq),
        "issued_at_utc": utc_now_iso(),
        "issued_at_local": local_now_iso(),
    }
    if extra:
        env["extra"] = extra
    return env


def write_atomic(path: Path, data: bytes) -> dict[str, Any]:
    """Write locally, replace, re-read size. SMB-cache-safe. Never reports green on 0-byte."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp_path), str(path))
        got = path.read_bytes()
        if len(got) != len(data):
            return {"ok": False, "reason": "size-mismatch-after-copy",
                    "want": len(data), "got": len(got), "path": str(path)}
        if len(got) == 0:
            return {"ok": False, "reason": "zero-byte-after-write", "path": str(path)}
        if got != data:
            return {"ok": False, "reason": "content-mismatch-after-copy", "path": str(path)}
        return {"ok": True, "path": str(path), "bytes": len(got),
                "sha256": sha256_bytes(got)}
    except Exception as exc:  # noqa: BLE001
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        return {"ok": False, "reason": f"{type(exc).__name__}: {exc}", "path": str(path)}


def dumps(env: dict[str, Any]) -> bytes:
    return (json.dumps(env, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


if __name__ == "__main__":
    sample = make_envelope(
        receiver=RECEIVER_SENSORIUM,
        task_id="smoke",
        claim="smoke",
        raw=[{"command": "echo ok", "stdout": "ok\n", "stderr": "", "exit": 0,
              "ts": utc_now_iso()}],
        reproduction_command="echo ok",
        goal="smoke",
        decisions=[],
        artifacts=[],
        uncertainty_notes=[],
        escalation_on_fail="owner",
    )
    errs = validate_envelope(sample)
    assert errs == [], errs
    print("OK envelope smoke")
