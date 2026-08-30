# -*- coding: utf-8 -*-
"""A3 — cognition quota + receipt attribution (telegram closed loop).

Old receipts are classified forensically and never rewritten.
UNATTRIBUTED rows cannot justify cognitive spend.
used >= cap → LOCAL_DEGRADED_MODE, zero network request.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path

_OPS = Path(__file__).resolve().parent
STATE = _OPS / "state"
RECEIPTS = STATE / "cortex" / "cost-receipts.jsonl"
PAID = STATE / "paid-calls.jsonl"

BUCKETS = ("K9", "event_probe", "full_loop", "telegram_normal", "judge_phase2")
REQUIRED = (
    "receipt_id", "task_id", "run_id", "turn_id", "provider", "model",
    "request_id", "status", "tokens", "cost_aud", "created_at",
    "process_id", "code_version",
)
DEFAULT_CAPS = {
    "K9": 80,
    "event_probe": 1,
    "full_loop": 12,
    "telegram_normal": 30,
    "judge_phase2": 20,
}


def classify_receipt(row: dict) -> dict:
    """Forensic label. Does not mutate the stored file."""
    task = str(row.get("task_id") or "").strip()
    run = str(row.get("run_id") or "").strip()
    attributed = bool(task) and bool(run)
    missing = [k for k in REQUIRED if not str(row.get(k) or "").strip()
               and k not in ("tokens", "cost_aud")]
    # tokens/cost may be numeric 0
    if row.get("tokens") in (None, ""):
        missing.append("tokens")
    if row.get("cost_aud") in (None, "") and row.get("estimated_or_reported_cost_aud") in (None, ""):
        missing.append("cost_aud")
    return {
        "attribution": "ATTRIBUTED" if attributed else "UNATTRIBUTED",
        "cognitive_quota_eligible": attributed,
        "missing_fields": missing,
        "task_id": task or None,
        "run_id": run or None,
    }


def forensic_scan_since(path: Path | None = None, *, since_iso: str,
                        limit: int = 5000) -> dict:
    """Coverage after migration timestamp. Historic rows are ignored, not rewritten."""
    p = Path(path) if path is not None else RECEIPTS
    n = attributed = 0
    if p.exists():
        with p.open(encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                ts = str(row.get("created_at") or row.get("request_timestamp") or "")
                if ts < since_iso:
                    continue
                n += 1
                if classify_receipt(row)["cognitive_quota_eligible"]:
                    attributed += 1
    unattr = n - attributed
    return {
        "n": n,
        "attributed": attributed,
        "unattributed": unattr,
        "attribution_ratio": (attributed / n) if n else None,
        "rewritten": 0,
        "since_iso": since_iso,
        "note": "post-migration coverage only",
    }


def forensic_scan(path: Path | None = None, *, limit: int = 5000) -> dict:
    p = Path(path) if path is not None else RECEIPTS
    n = attributed = 0
    if p.exists():
        with p.open(encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                n += 1
                if classify_receipt(row)["cognitive_quota_eligible"]:
                    attributed += 1
    unattr = n - attributed
    return {
        "n": n,
        "attributed": attributed,
        "unattributed": unattr,
        "attribution_ratio": (attributed / n) if n else None,
        "rewritten": 0,
        "note": "98-class historic UNATTRIBUTED rows are labeled, not rewritten",
    }


def stamp_new_receipt(base: dict, *, task_id: str, run_id: str, turn_id: str,
                      bucket: str, code_version: str = "closed-loop/2026-08-20") -> dict:
    rec = dict(base)
    rec["receipt_id"] = rec.get("receipt_id") or ("rcp-" + uuid.uuid4().hex[:16])
    rec["task_id"] = str(task_id)
    rec["run_id"] = str(run_id)
    rec["turn_id"] = str(turn_id)
    rec["request_id"] = rec.get("request_id") or rec.get("trace_id") or rec["receipt_id"]
    rec["provider"] = rec.get("provider") or rec.get("exact_model") or ""
    rec["model"] = rec.get("model") or rec.get("exact_model") or ""
    rec["status"] = rec.get("status") or rec.get("receipt_status") or "COMPLETE"
    rec["tokens"] = rec.get("tokens")
    if rec["tokens"] is None:
        tin = rec.get("prompt_tokens")
        tout = rec.get("completion_tokens")
        try:
            rec["tokens"] = int(tin or 0) + int(tout or 0)
        except (TypeError, ValueError):
            rec["tokens"] = 0
    rec["cost_aud"] = rec.get("cost_aud")
    if rec["cost_aud"] is None:
        rec["cost_aud"] = rec.get("estimated_or_reported_cost_aud")
    rec["created_at"] = rec.get("created_at") or rec.get("response_timestamp") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rec["process_id"] = rec.get("process_id") or os.getpid()
    rec["code_version"] = rec.get("code_version") or code_version
    rec["bucket"] = bucket if bucket in BUCKETS else "telegram_normal"
    rec["attribution"] = "ATTRIBUTED"
    rec["cognitive_quota_eligible"] = True
    return rec


def _cap(bucket: str) -> int:
    env = os.environ.get(f"OCTOPUS_COGNITION_CAP_{bucket.upper()}")
    if env:
        try:
            return max(0, int(env))
        except ValueError:
            pass
    return int(DEFAULT_CAPS.get(bucket, 30))


def used_eligible(path: Path | None = None, *, bucket: str = "telegram_normal") -> int:
    p = Path(path) if path is not None else RECEIPTS
    n = 0
    if not p.exists():
        return 0
    with p.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if str(row.get("bucket") or "") != bucket:
                continue
            if classify_receipt(row)["cognitive_quota_eligible"]:
                n += 1
    return n


def gate_paid_intent(*, task: str = "", run_id: str = "",
                     bucket: str = "telegram_normal",
                     receipts_path: Path | None = None,
                     paid_paused: bool | None = None) -> dict:
    """Call BEFORE write-ahead / network. Fail-closed."""
    bucket = bucket if bucket in BUCKETS else "telegram_normal"
    if paid_paused is None:
        paid_paused = os.environ.get("OCTOPUS_PAID_COGNITION", "0") != "1"
    if paid_paused:
        return {"allow": False, "reason": "PAID_COGNITION_PAUSED",
                "mode": "LOCAL_DEGRADED_MODE"}
    task = str(task or "").strip()
    run_id = str(run_id or os.environ.get("OCTOPUS_RUN_ID") or "").strip()
    if not task or not run_id:
        return {"allow": False, "reason": "UNATTRIBUTED_INTENT_BLOCKED",
                "mode": "LOCAL_DEGRADED_MODE"}
    used = used_eligible(receipts_path, bucket=bucket)
    cap = _cap(bucket)
    if used >= cap:
        return {"allow": False, "reason": "QUOTA_EXHAUSTED",
                "mode": "LOCAL_DEGRADED_MODE", "used": used, "cap": cap}
    return {"allow": True, "reason": "ok", "used": used, "cap": cap,
            "task_id": task, "run_id": run_id, "bucket": bucket}


def intent_fingerprint(need: str, target: str, capability: str) -> str:
    blob = f"{need}|{target}|{capability}".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]
