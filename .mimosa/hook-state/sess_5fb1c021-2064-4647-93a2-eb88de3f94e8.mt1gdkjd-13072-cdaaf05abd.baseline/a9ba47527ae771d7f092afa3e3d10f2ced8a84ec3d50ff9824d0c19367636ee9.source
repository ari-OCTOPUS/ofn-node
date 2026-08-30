#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A0 baseline snapshot. No Telegram API. No secrets. No rewrite of receipts."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPS = ROOT / "_ops"
OUT = Path(__file__).resolve().parent
LANE = [
    OPS / "telegram_center" / "center.py",
    OPS / "telegram_center" / "input_surface_policy.py",
    OPS / "owner_console" / "local_commands.py",
    OPS / "owner_console" / "telegram_adapter.py",
    OPS / "owner_console" / "conversation.py",
    OPS / "cognition_quota.py",
    OPS / "cortex" / "cost_receipt.py",
    OPS / "cortex" / "model_router.py",
    OPS / "spine" / "spine_adapters.py",
    OPS / "tests" / "test_telegram_closed_loop_20260820.py",
]


def sha256(p: Path) -> dict:
    if not p.exists():
        return {"path": str(p.relative_to(ROOT)).replace("\\", "/"),
                "exists": False}
    st = p.stat()
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "exists": True, "sha256": h, "bytes": st.st_size,
            "mtime": int(st.st_mtime)}


def pids() -> dict:
    cmd = [
        "powershell", "-NoProfile", "-Command",
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" | "
        "Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress",
    ]
    try:
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL,
                                      timeout=30)
        rows = json.loads(raw or "[]")
        if isinstance(rows, dict):
            rows = [rows]
    except (subprocess.SubprocessError, ValueError):
        rows = []
    want = ("center.py", "approval_channel", "organism.py", "brain.daemon",
            "miniapp_gateway")
    hit = {k: [] for k in ("center", "approval_channel", "organism",
                            "brain.daemon", "other_tg")}
    n_center = 0
    for r in rows:
        cl = str(r.get("CommandLine") or "")
        pid = r.get("ProcessId")
        if "center.py" in cl:
            hit["center"].append({"pid": pid, "cmd": cl[:220]})
            n_center += 1
        elif "approval_channel" in cl:
            hit["approval_channel"].append({"pid": pid, "cmd": cl[:220]})
        elif cl.rstrip().endswith("organism.py") or " organism.py" in cl:
            hit["organism"].append({"pid": pid, "cmd": cl[:220]})
        elif "brain.daemon" in cl or "-m brain.daemon" in cl:
            hit["brain.daemon"].append({"pid": pid, "cmd": cl[:220]})
        elif "miniapp_gateway" in cl or "telegram" in cl.lower():
            hit["other_tg"].append({"pid": pid, "cmd": cl[:220]})
    hit["canonical_inbound_count"] = n_center
    return hit


def jsonl_n(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                n += 1
    return n


def inbound_cmds(path: Path, *, last: int = 30) -> dict:
    rows = []
    if path.exists():
        with path.open(encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    cmds = {}
    for r in rows:
        c = str(r.get("cmd") or "")
        if c:
            cmds[c] = cmds.get(c, 0) + 1
    last_rows = []
    for r in rows[-last:]:
        last_rows.append({
            "update_id": r.get("update_id"),
            "cmd": r.get("cmd"),
            "is_command": r.get("is_command"),
            "from_owner": r.get("from_owner"),
            "bot": r.get("bot"),
            "ts": r.get("ts"),
            "chars": r.get("chars"),
        })
    return {"n": len(rows), "cmd_counts": cmds, "last": last_rows}


def spine_telegram() -> dict:
    db = OPS / "state" / "spine" / "spine.db"
    if not db.exists():
        return {"exists": False, "n_telegram": 0}
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        n = con.execute(
            "SELECT COUNT(*) FROM events WHERE domain='telegram'").fetchone()[0]
        last = con.execute(
            "SELECT event_id, idempotency_key, producer, occurred_at, "
            "event_time_source FROM events WHERE domain='telegram' "
            "ORDER BY rowid DESC LIMIT 5").fetchall()
        con.close()
        return {"exists": True, "n_telegram": n,
                "last": [dict(zip(
                    ("event_id", "idempotency_key", "producer",
                     "occurred_at", "event_time_source"), x)) for x in last]}
    except sqlite3.Error as e:
        return {"exists": True, "error": type(e).__name__, "n_telegram": None}


def git_head() -> dict:
    def _g(*a):
        try:
            return subprocess.check_output(
                ["git", "-C", str(ROOT), *a], text=True,
                stderr=subprocess.DEVNULL, timeout=20).strip()
        except subprocess.SubprocessError:
            return ""
    return {"branch": _g("rev-parse", "--abbrev-ref", "HEAD"),
            "commit": _g("rev-parse", "--short", "HEAD")}


def main() -> int:
    sys.path.insert(0, str(OPS))
    from cognition_quota import forensic_scan  # noqa: WPS433

    lock = json.loads((OPS / "state/locks/octopus-writer.lock").read_text(
        encoding="utf-8"))
    now = time.time()
    remaining = lock["acquired_at"] + lock["ttl_seconds"] - now
    forensic = forensic_scan()
    paid = OPS / "state" / "paid-calls.jsonl"
    receipts = OPS / "state" / "cortex" / "cost-receipts.jsonl"
    inbound = OPS / "state" / "telegram" / "inbound-log.jsonl"
    sendlog = OPS / "state" / "tg-send-log.jsonl"
    stop = OPS / "state" / "telegram" / "owner-stop.flag"
    pack = {
        "schema": "telegram-closed-loop-a0/1",
        "captured_at_unix": now,
        "lease": {**lock, "remaining_s": remaining, "valid": remaining > 0},
        "bots_frozen": {
            "canonical_owner": {"id": 7992324219, "handle": "@intergrade2725_Bot"},
            "approval": {"id": 8187434784, "handle": "@Robo2725_bot"},
            "ziman": {"id": 8861821707},
        },
        "pids": pids(),
        "paid_cognition_env": os.environ.get("OCTOPUS_PAID_COGNITION", "UNSET"),
        "wire_spine_env": os.environ.get("OCTOPUS_WIRE_SPINE", "UNSET"),
        "t48_env": os.environ.get("OCTOPUS_T48_EVENT_TIME", "UNSET"),
        "owner_stop_flag": stop.exists(),
        "lane_manifest": [sha256(p) for p in LANE],
        "forensic_receipts": forensic,
        "counts": {
            "cost_receipts": jsonl_n(receipts),
            "paid_calls": jsonl_n(paid),
            "tg_send_log": jsonl_n(sendlog),
        },
        "inbound": inbound_cmds(inbound),
        "spine": spine_telegram(),
        "git": git_head(),
        "live_b": "BLOCKED",
        "full_loop": "PAUSED_UNTIL_A7_GATES",
        "paid_cognition_policy": "off_until_A4_code_ready_live_process_not_reloaded",
    }
    (OUT / "A0-BASELINE.json").write_text(
        json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "wrote": str(OUT / "A0-BASELINE.json"),
        "lease_remaining_s": round(remaining),
        "center_pids": pack["pids"]["center"],
        "canonical_inbound_count": pack["pids"]["canonical_inbound_count"],
        "spine_telegram": pack["spine"].get("n_telegram"),
        "receipts": forensic,
        "git": pack["git"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
