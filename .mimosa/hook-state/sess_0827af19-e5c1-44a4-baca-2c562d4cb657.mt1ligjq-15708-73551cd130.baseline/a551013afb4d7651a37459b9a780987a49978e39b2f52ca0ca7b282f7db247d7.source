# -*- coding: utf-8 -*-
"""Phase-1 shadow adapter: v2 ledger beside original receipts.

Never rewrites the source jsonl. Never fabricates task_id from PID,
timestamp, capability, or current process env. Restart is out of scope.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import receipt_v2

ADAPTER_VERSION = "v2"
SCHEMA = "receipt-v2-shadow/1"
SOURCES = ("context", "caller", "legacy_missing")
STATUSES = ("resolved", "unresolved")
REQUIRED = (
    "receipt_id", "timestamp_utc", "task_id", "run_id", "agent_id",
    "capability_id", "outcome", "evidence_ref", "schema_version",
    "task_id_source", "attribution_status", "original_receipt_hash",
    "adapter_version",
)

_OPS = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = _OPS / "state" / "cortex" / "cost-receipts.jsonl"
DEFAULT_SHADOW = _OPS.parent / "06-EVIDENCE" / "NERVOUS-RECOVERY-2026-08-20" / "receipts-v2-shadow.jsonl"
CONTEXT_PATH = _OPS / "state" / "cortex" / "active-task-context.json"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def original_receipt_hash(raw_line: str | dict) -> str:
    if isinstance(raw_line, dict):
        blob = json.dumps(raw_line, sort_keys=True, ensure_ascii=False, default=str)
    else:
        blob = raw_line.rstrip("\n")
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_run_to_task(path: Path | None = None) -> dict[str, str]:
    """Explicit run_id → task_id map only. Empty file / missing → {}."""
    p = Path(path or CONTEXT_PATH)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out: dict[str, str] = {}
    if isinstance(data, dict):
        mapping = data.get("run_to_task")
        if isinstance(mapping, dict):
            for k, v in mapping.items():
                ks, vs = str(k).strip(), str(v or "").strip()
                if ks and vs:
                    out[ks] = vs
        run = str(data.get("run_id") or "").strip()
        task = str(data.get("task_id") or "").strip()
        if run and task:
            out[run] = task
    return out


def _resolve(row: dict, run_to_task: dict[str, str]) -> tuple[str | None, str, str]:
    caller = str(row.get("task_id") or "").strip()
    if caller:
        return caller, "caller", "resolved"
    run = str(row.get("run_id") or "").strip()
    if run and run in run_to_task:
        mapped = str(run_to_task[run]).strip()
        if mapped:
            return mapped, "context", "resolved"
    return None, "legacy_missing", "unresolved"


def shadow_one(row: dict, *, run_to_task: dict[str, str] | None = None,
               raw_line: str | None = None) -> dict[str, Any]:
    """Build a v2 shadow record. Does not mutate `row`."""
    src = dict(row)
    mapping = run_to_task or {}
    task, source, status = _resolve(src, mapping)
    run = str(src.get("run_id") or "").strip()
    env = receipt_v2.envelope(
        task_id=task,
        run_id=run or None,
        agent_id=str(src.get("process_id") or src.get("agent_id") or "legacy"),
        capability_id=str(src.get("capability_id") or "model.call.paid"),
        outcome="ok" if status == "resolved" else "unattributed",
        evidence_ref=str(src.get("trace_id") or src.get("receipt_id") or ""),
        timestamp_utc=str(src.get("created_at") or src.get("request_timestamp")
                          or src.get("ts") or _utc()),
        receipt_id=str(src.get("receipt_id") or "") or None,
    )
    # JSON null, not a synthesized id. envelope() used "" for missing; override.
    env["task_id"] = task
    if status == "unresolved":
        env["outcome"] = "unattributed"
        env["task_id"] = None
    env["task_id_source"] = source
    env["attribution_status"] = status
    env["original_receipt_hash"] = original_receipt_hash(raw_line if raw_line is not None else src)
    env["adapter_version"] = ADAPTER_VERSION
    env["shadow"] = True
    env["rewrites_original"] = False
    return env


def schema_errors(env: dict) -> list[str]:
    errs: list[str] = []
    for k in REQUIRED:
        if k not in env:
            errs.append(f"missing:{k}")
    if env.get("schema_version") != 2:
        errs.append("schema_version")
    if env.get("adapter_version") != ADAPTER_VERSION:
        errs.append("adapter_version")
    if env.get("task_id_source") not in SOURCES:
        errs.append("task_id_source")
    if env.get("attribution_status") not in STATUSES:
        errs.append("attribution_status")
    if env.get("attribution_status") == "unresolved" and env.get("task_id") not in (None, ""):
        errs.append("unresolved_must_be_null")
    if env.get("attribution_status") == "resolved" and not str(env.get("task_id") or "").strip():
        errs.append("resolved_missing_task_id")
    h = str(env.get("original_receipt_hash") or "")
    if len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
        errs.append("original_receipt_hash")
    return errs


def _is_fabricated(env: dict, row: dict, run_to_task: dict[str, str]) -> bool:
    source = env.get("task_id_source")
    tid = env.get("task_id")
    if source == "legacy_missing":
        return tid not in (None, "")
    if source == "caller":
        return str(tid or "") != str(row.get("task_id") or "").strip()
    if source == "context":
        run = str(row.get("run_id") or "").strip()
        expected = run_to_task.get(run, "")
        return str(tid or "") != str(expected)
    return True


def evaluate_window(
    source: Path | None = None,
    *,
    since_iso: str | None = None,
    run_to_task: dict[str, str] | None = None,
    limit: int = 200000,
) -> dict[str, Any]:
    """Hygiene of a source window. Does not write a shadow ledger."""
    src = Path(source or DEFAULT_SOURCE)
    mapping = dict(run_to_task) if run_to_task is not None else load_run_to_task()
    n_src = 0
    n_bad_json = 0
    n_skipped_old = 0
    fabricated = 0
    schema_fail = 0
    hashes: list[str] = []
    if src.exists():
        with src.open(encoding="utf-8", errors="replace") as f_in:
            for i, line in enumerate(f_in):
                if i >= limit:
                    break
                raw = line.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except ValueError:
                    n_bad_json += 1
                    continue
                if since_iso:
                    ts = str(row.get("created_at") or row.get("request_timestamp")
                             or row.get("ts") or "")
                    if ts and ts < since_iso:
                        n_skipped_old += 1
                        continue
                n_src += 1
                env = shadow_one(row, run_to_task=mapping, raw_line=raw)
                hashes.append(env["original_receipt_hash"])
                if schema_errors(env):
                    schema_fail += 1
                if _is_fabricated(env, row, mapping):
                    fabricated += 1
    dup_in_window = len(hashes) - len(set(hashes))
    n_hashed = sum(1 for h in hashes if len(h) == 64)
    coverage = (n_hashed / n_src) if n_src else 0.0
    schema_ok = (n_src - schema_fail) / n_src if n_src else 0.0
    criteria = {
        "duplicate_receipts": dup_in_window,
        "fabricated_task_ids": fabricated,
        "schema_validation": round(schema_ok, 4),
        "original_receipt_hash_coverage": round(coverage, 4),
    }
    passed = (
        n_src > 0
        and criteria["duplicate_receipts"] == 0
        and criteria["fabricated_task_ids"] == 0
        and criteria["schema_validation"] == 1.0
        and criteria["original_receipt_hash_coverage"] == 1.0
    )
    return {
        "schema": SCHEMA,
        "mode": "preview",
        "rewrites_original": False,
        "n_source_in_window": n_src,
        "n_skipped_old": n_skipped_old,
        "n_bad_json": n_bad_json,
        "criteria": criteria,
        "shadow_pass": passed,
        "wave1_unlocked": False,
    }


def scan_to_shadow(
    source: Path | None = None,
    dest: Path | None = None,
    *,
    since_iso: str | None = None,
    run_to_task: dict[str, str] | None = None,
    limit: int = 200000,
) -> dict[str, Any]:
    """Read original jsonl, append v2 shadow rows. Source file is never opened for write."""
    src = Path(source or DEFAULT_SOURCE)
    out = Path(dest or DEFAULT_SHADOW)
    mapping = dict(run_to_task) if run_to_task is not None else load_run_to_task()
    existing_hashes: set[str] = set()
    if out.exists():
        with out.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    prev = json.loads(line)
                except ValueError:
                    continue
                h = str(prev.get("original_receipt_hash") or "")
                if h:
                    existing_hashes.add(h)

    n_src = 0
    n_written = 0
    n_skipped_dup = 0
    n_skipped_old = 0
    n_bad_json = 0
    fabricated = 0
    schema_fail = 0
    hashes_this_run: list[str] = []
    out.parent.mkdir(parents=True, exist_ok=True)

    if src.exists():
        with src.open(encoding="utf-8", errors="replace") as f_in, \
                out.open("a", encoding="utf-8") as f_out:
            for i, line in enumerate(f_in):
                if i >= limit:
                    break
                raw = line.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except ValueError:
                    n_bad_json += 1
                    continue
                if since_iso:
                    ts = str(row.get("created_at") or row.get("request_timestamp")
                             or row.get("ts") or "")
                    if ts and ts < since_iso:
                        n_skipped_old += 1
                        continue
                n_src += 1
                env = shadow_one(row, run_to_task=mapping, raw_line=raw)
                h = env["original_receipt_hash"]
                hashes_this_run.append(h)
                if schema_errors(env):
                    schema_fail += 1
                if _is_fabricated(env, row, mapping):
                    fabricated += 1
                if h in existing_hashes:
                    n_skipped_dup += 1
                    continue
                f_out.write(json.dumps(env, ensure_ascii=False) + "\n")
                existing_hashes.add(h)
                n_written += 1

    dup_in_window = len(hashes_this_run) - len(set(hashes_this_run))
    coverage = 1.0 if n_src == 0 else (n_written + n_skipped_dup) / n_src
    schema_ok = 1.0 if n_src == 0 else (n_src - schema_fail) / n_src
    criteria = {
        "duplicate_receipts": dup_in_window,
        "fabricated_task_ids": fabricated,
        "schema_validation": round(schema_ok, 4),
        "original_receipt_hash_coverage": round(coverage, 4),
    }
    passed = (
        criteria["duplicate_receipts"] == 0
        and criteria["fabricated_task_ids"] == 0
        and criteria["schema_validation"] == 1.0
        and criteria["original_receipt_hash_coverage"] == 1.0
        and n_src > 0
    )
    return {
        "schema": SCHEMA,
        "ts": _utc(),
        "source": str(src),
        "dest": str(out),
        "rewrites_original": False,
        "n_source_in_window": n_src,
        "n_written": n_written,
        "n_skipped_duplicate_hash": n_skipped_dup,
        "n_skipped_old": n_skipped_old,
        "n_bad_json": n_bad_json,
        "wave1_unlocked": False,
        "criteria": criteria,
        "shadow_pass": passed,
        "note": "PASS here is shadow-window hygiene, not WAVE0_PASS",
    }


if __name__ == "__main__":
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rep = scan_to_shadow(since_iso=today)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
