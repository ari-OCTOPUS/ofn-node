# -*- coding: utf-8 -*-
"""Index-based self scanner. Never walks the whole vault. Each record has
freshness / source / hash / task identity / confidence."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import OPS_DIR, ROOT
from .contracts import sha256_file, utc_now

# Explicit index — no recursive glob over the vault.
_SOURCES: list[tuple[str, str]] = [
    ("capsule", "07 - Knowledge/شناخت-اختاپوس/جلسات/CURRENT-SESSION-CAPSULE.md"),
    ("harvest-75", "07 - Knowledge/شناخت-اختاپوس/75-SESSION-HARVEST-WAVE0-TELEGRAM-2026-08-21.md"),
    ("learning-ledger", "06-EVIDENCE/SESSION-HARVEST-2026-08-21/LEARNING-LEDGER.jsonl"),
    ("needs-ledger", "06-EVIDENCE/SESSION-HARVEST-2026-08-21/NEEDS-LEDGER.jsonl"),
    ("loop-registry", "_ops/state/loops/LOOP-REGISTRY.json"),
    ("capability-inventory", "_ops/state/coordination/CAPABILITY-INVENTORY-2026-08-21.json"),
    ("execution-manifest", "_ops/state/loops/execution-manifest.jsonl"),
    ("wave1-preflight", "_ops/state/waves/WAVE1-PREFLIGHT-2026-08-21.json"),
    ("triage-51", "_ops/state/loops/TRIAGE-51-FAILURES-2026-08-21.md"),
    ("heartbeat", "_memory/HEARTBEAT.md"),
    ("calibration", "_ops/state/cortex/calibration-latest.json"),
    ("self-knowledge", "_ops/state/doctor/self-knowledge-latest.json"),
    ("memory-read-last", "_ops/state/pulse/memory-read-last.json"),
    ("blocker-queue", "_ops/state/coordination/BLOCKER-QUEUE.jsonl"),
]


def _age_hours(path: Path) -> float | None:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return None
    return (datetime.now(timezone.utc).timestamp() - mtime) / 3600.0


def _record(role: str, rel: str, extra: dict | None = None) -> dict[str, Any]:
    path = ROOT / rel
    rec: dict[str, Any] = {
        "role": role,
        "source": rel.replace("\\", "/"),
        "task_id": f"scan:{role}",
        "run_id": f"self-scan:{utc_now()}",
        "exists": path.is_file(),
        "hash": "",
        "freshness_hours": None,
        "confidence": 0.0,
        "bytes": 0,
    }
    if not path.is_file():
        rec["note"] = "missing"
        return rec
    try:
        rec["bytes"] = int(path.stat().st_size)
    except OSError:
        rec["bytes"] = 0
    rec["hash"] = sha256_file(path)[:16]
    rec["freshness_hours"] = round(_age_hours(path) or 0.0, 3)
    age = rec["freshness_hours"]
    rec["confidence"] = 0.92 if age <= 48 else (0.7 if age <= 168 else 0.4)
    if extra:
        rec.update(extra)
    return rec


def _tail_jsonl(path: Path, n: int = 8) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out = []
    for line in lines[-n:]:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if isinstance(rec, dict):
            out.append({k: rec.get(k) for k in list(rec)[:8]})
    return out


def scan(*, include_git: bool = True) -> dict[str, Any]:
    """Bounded index scan. Git history is `git log -15 --oneline` only."""
    files = [_record(role, rel) for role, rel in _SOURCES]
    registry = ROOT / "_ops/state/loops/LOOP-REGISTRY.json"
    open_loops: list[dict] = []
    if registry.is_file():
        try:
            data = json.loads(registry.read_text(encoding="utf-8"))
            for e in (data.get("entries") or []) + (data.get("incidents") or []):
                st = str(e.get("status") or "").lower()
                if st in ("open", "in_progress", "locked"):
                    open_loops.append({
                        "loop_id": e.get("loop_id") or e.get("seam_id"),
                        "status": e.get("status"),
                        "severity": e.get("severity"),
                        "title": (e.get("title") or e.get("note") or "")[:160],
                    })
        except (OSError, ValueError):
            pass
    needs = []
    np = ROOT / "06-EVIDENCE/SESSION-HARVEST-2026-08-21/NEEDS-LEDGER.jsonl"
    if np.is_file():
        needs = _tail_jsonl(np, 20)
    git: dict[str, Any] = {}
    if include_git:
        import subprocess
        try:
            r = subprocess.run(
                ["git", "log", "-12", "--oneline"],
                cwd=str(ROOT), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=20)
            git = {"head_lines": [ln for ln in r.stdout.splitlines() if ln][:12],
                   "ok": r.returncode == 0}
        except Exception as exc:  # noqa: BLE001
            git = {"ok": False, "error": type(exc).__name__}
    preflight = None
    pf = ROOT / "_ops/state/waves/WAVE1-PREFLIGHT-2026-08-21.json"
    if pf.is_file():
        try:
            preflight = json.loads(pf.read_text(encoding="utf-8"))
        except ValueError:
            preflight = {"corrupt": True}
    return {
        "schema": "self-scan/1",
        "ts": utc_now(),
        "files": files,
        "open_loops": open_loops[:40],
        "needs": needs,
        "git": git,
        "wave1_preflight": {
            "wave1_unlocked": (preflight or {}).get("wave1_unlocked"),
            "blockers": ((preflight or {}).get("verdict") or {}).get("blockers"),
            "next_unit": ((preflight or {}).get("verdict") or {}).get("next_unit"),
        } if preflight else None,
        "paid_calls": "FORBIDDEN",
        "recursive_vault_scan": False,
    }
