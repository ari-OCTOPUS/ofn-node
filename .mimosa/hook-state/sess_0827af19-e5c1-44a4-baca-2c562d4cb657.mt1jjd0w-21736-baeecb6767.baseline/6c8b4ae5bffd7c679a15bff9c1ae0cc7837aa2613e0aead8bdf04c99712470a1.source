#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""kernel_bridge_reader.py — read-only shadow reader for body_bridge outputs (WP-D).

هدف: یک reader امن و فقط‌خواندنی در داخلِ _ops که structured outputهای
body_bridge را می‌خواند — بدون اینکه هیچ‌چیز از 4d_system import کند.

قرارداد مرز (contract boundary):
  - فقط از body_bridge/output/*.json و *.jsonl می‌خواند.
  - هیچ import از 4d_system ندارد.
  - هیچ write از kernel به _ops/state نمی‌دهد.
  - هیچ production decision change نمی‌دهد.
  - timeout/failure => no-op + explicit degraded status.
  - default OFF (پشتِ OCTOPUS_WIRE_KERNEL_BRIDGE_READER).

تفکیک freshness:
  fresh   — artifact کمتر از max_age_h ساعت پیش به‌روز شده
  stale   — artifact قدیمی‌تر از max_age_h
  missing — artifact موجود نیست
  corrupt — artifact موجود ولی غیرقابل‌پارس
  incompatible — artifact موجود و معقول ولی schema ناسازگار

هیچ‌کدام به empty/healthy تبدیل نمی‌شوند.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# body_bridge output directory (relative to repo root)
BRIDGE_OUTPUT = _HERE.parent / "03 - Projects" / "research-spec-compiler" / "body_bridge" / "output"

# Status report path (inside _ops/state — this is the ONLY write, and it's a
# shadow/observability report, never consumed by a production decision).
REPORT_PATH = _HERE / "state" / "kernel-bridge-reader-report.json"

SCHEMA = "KernelBridgeReaderReport.v1"
DEFAULT_MAX_AGE_H = 48  # an output older than 48h is stale


def _is_enabled() -> bool:
    return os.environ.get("OCTOPUS_WIRE_KERNEL_BRIDGE_READER", "0") == "1"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path) -> tuple[dict | None, str]:
    """Read JSON. Returns (data, status) where status is ok|missing|corrupt."""
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text("utf-8")), "ok"
    except (OSError, ValueError):
        return None, "corrupt"


def _read_jsonl(path: Path) -> tuple[list[dict], int, str]:
    """Read JSONL. Returns (rows, corrupt_count, status)."""
    if not path.exists():
        return [], 0, "missing"
    rows = []
    corrupt = 0
    try:
        for line in path.read_text("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                corrupt += 1
    except OSError:
        return [], 0, "corrupt"
    status = "ok" if corrupt == 0 else "corrupt"
    return rows, corrupt, status


def _check_freshness(path: Path, max_age_h: float = DEFAULT_MAX_AGE_H) -> str:
    """Check artifact freshness based on mtime. Returns fresh|stale|missing."""
    if not path.exists():
        return "missing"
    try:
        mtime = path.stat().st_mtime
        age_h = (time.time() - mtime) / 3600
        return "fresh" if age_h < max_age_h else "stale"
    except OSError:
        return "missing"


def _check_schema_compat(data: dict, expected_keys: list[str]) -> str:
    """Check if data has expected top-level keys."""
    if not isinstance(data, dict):
        return "incompatible"
    missing = [k for k in expected_keys if k not in data]
    if missing:
        return "incompatible"
    return "ok"


def read_status(max_age_h: float = DEFAULT_MAX_AGE_H) -> dict:
    """Read all bridge outputs and return a structured status report.

    This is the main entry point. It never raises — failures degrade to
    explicit per-artifact status.
    """
    artifacts = {
        "manifest": {
            "path": BRIDGE_OUTPUT / "manifest.json",
            "jsonl": False,
            "expected_keys": ["generated_at", "schema"],
        },
        "adr_feed": {
            "path": BRIDGE_OUTPUT / "adr_feed.json",
            "jsonl": False,
            "expected_keys": ["adrs", "generated_at"],
        },
        "verdict_stream": {
            "path": BRIDGE_OUTPUT / "verdict_stream.jsonl",
            "jsonl": True,
        },
        "kernel_dashboard": {
            "path": BRIDGE_OUTPUT / "kernel_dashboard.json",
            "jsonl": False,
            "expected_keys": ["manifest", "adr_feed", "verdict_stream"],
        },
    }

    results = {}
    overall_ok = True

    for name, spec in artifacts.items():
        path = spec["path"]
        freshness = _check_freshness(path, max_age_h)
        integrity = "ok"
        schema_compat = "ok"
        detail = {}

        if spec.get("jsonl"):
            rows, corrupt, status = _read_jsonl(path)
            integrity = status
            detail = {"n_rows": len(rows), "corrupt_lines": corrupt}
            if status != "ok":
                overall_ok = False
        else:
            data, status = _read_json(path)
            integrity = status
            if data is not None:
                schema_compat = _check_schema_compat(data, spec.get("expected_keys", []))
                detail = {"top_keys": sorted(data.keys())[:10]}
            if status != "ok" or schema_compat != "ok":
                overall_ok = False

        # Freshness failure doesn't make overall_ok false, but it's noted
        if freshness == "missing":
            overall_ok = False

        results[name] = {
            "path": str(path),
            "freshness": freshness,
            "integrity": integrity,
            "schema_compat": schema_compat,
            "detail": detail,
        }

    report = {
        "schema": SCHEMA,
        "ts": _utc_iso(),
        "enabled": _is_enabled(),
        "overall_ok": overall_ok,
        "max_age_h": max_age_h,
        "bridge_output_dir": str(BRIDGE_OUTPUT),
        "artifacts": results,
        "note": ("Shadow reader (default OFF). Reads body_bridge outputs only; "
                 "never imports 4d_system; never writes to _ops/state decisions."),
    }

    return report


def persist_report(report: dict | None = None) -> dict:
    """Write the status report to REPORT_PATH (observability only)."""
    if not _is_enabled():
        return {"ok": False, "reason": "disabled"}
    if report is None:
        report = read_status()
    try:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), "utf-8")
    except OSError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, "path": str(REPORT_PATH)}


if __name__ == "__main__":
    r = read_status()
    print(json.dumps(r, ensure_ascii=False, indent=2))
