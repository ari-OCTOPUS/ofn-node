#!/usr/bin/env python3
"""LOOP-LIVE-ORPHAN-MISSING-SUPERVISION watchdog (Unit 3, 2026-08-21).

Detects the alive-child / dead-parent state of the Telegram miniapp gateway
without restarting a healthy child. Recovery is bounded: a missing gateway
may be restarted at most RESTART_MAX times per window with a cooldown; an
orphaned-but-alive child is only reported (never restarted). Every decision
is written as a receipt to state/orphan-watchdog/receipts.jsonl.

Pure core (classify / recovery_plan) is injected-rows testable; the CLI path
executes restarts only inside the documented bounds.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent

GATEWAY_MARKER = "miniapp_gateway"
RESTART_MAX = 2          # per window
WINDOW_S = 3600
COOLDOWN_S = 600


def _state_dir() -> Path:
    base = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    return Path(base) if base else (_OPS / "state")


def receipts_path() -> Path:
    return _state_dir() / "orphan-watchdog" / "receipts.jsonl"


def state_path() -> Path:
    return _state_dir() / "orphan-watchdog" / "state.json"


def _cim_rows() -> list[dict]:
    """Process snapshot via PowerShell CIM (parameter list, no shell)."""
    script = ("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
              "ForEach-Object { [pscustomobject]@{Pid=$_.ProcessId;"
              "Parent=$_.ParentProcessId;Cmd=$_.CommandLine} } | "
              "ConvertTo-Json -Compress")
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30)
    except Exception:  # noqa: BLE001 — watchdog never dies on probe failure
        return []
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return []
    if isinstance(data, dict):
        data = [data]
    return [d for d in data if isinstance(d, dict)]


def snapshot(rows: list[dict] | None = None) -> list[dict]:
    """Gateways (command line contains the marker) from a process snapshot."""
    rows = rows if rows is not None else _cim_rows()
    out = []
    for r in rows:
        cmd = str(r.get("Cmd") or "")
        if GATEWAY_MARKER not in cmd:
            continue
        try:
            out.append({"pid": int(r["Pid"]), "parent": int(r.get("Parent") or 0),
                        "cmd": cmd})
        except (TypeError, ValueError, KeyError):
            continue
    return out


def alive_pids(rows: list[dict]) -> set[int]:
    out = {0}
    for r in rows:
        try:
            out.add(int(r.get("Pid")))
        except (TypeError, ValueError):
            continue
    return out


def classify(gateways: list[dict], rows: list[dict]) -> list[dict]:
    """Per-gateway state: HEALTHY (parent alive) or ORPHAN (parent gone)."""
    alive = alive_pids(rows)
    out = []
    for g in gateways:
        out.append({**g, "state": "ORPHAN" if g["parent"] not in alive else "HEALTHY"})
    return out


def _load_state() -> dict:
    p = state_path()
    try:
        if p.is_file():
            d = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(d, dict):
                return d
    except (OSError, ValueError):
        pass
    return {"window_start": 0.0, "restarts": 0, "last_restart_ts": 0.0,
            "cooldown_until": 0.0}


def _save_state(st: dict) -> None:
    try:
        p = state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _append_receipt(rec: dict) -> None:
    try:
        p = receipts_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def recovery_plan(gateways: list[dict], rows: list[dict],
                  state: dict | None = None, now: float | None = None) -> list[dict]:
    """Bounded recovery decisions. Never restarts a healthy/orphan child.

    - ORPHAN child: receipt only (report, no restart).
    - No gateway at all: RESTART if within budget and cooldown, else BLOCKED.
    """
    state = dict(state or _load_state())
    now = float(now if now is not None else time.time())
    actions = []
    classified = classify(gateways, rows)
    for g in classified:
        if g["state"] == "ORPHAN":
            actions.append({"kind": "orphan_receipt", "pid": g["pid"],
                            "parent": g["parent"], "state": "ORPHAN"})
    if not gateways:
        if now - float(state.get("window_start") or 0) >= WINDOW_S:
            state["window_start"] = now
            state["restarts"] = 0
        if now < float(state.get("cooldown_until") or 0):
            actions.append({"kind": "restart_blocked", "reason": "cooldown",
                            "retry_after_s": round(float(state["cooldown_until"]) - now, 1)})
        elif int(state.get("restarts") or 0) >= RESTART_MAX:
            actions.append({"kind": "restart_blocked", "reason": "budget_exhausted",
                            "window_start": state.get("window_start")})
        else:
            state["restarts"] = int(state.get("restarts") or 0) + 1
            state["last_restart_ts"] = now
            state["cooldown_until"] = now + COOLDOWN_S
            actions.append({"kind": "restart", "attempt": state["restarts"],
                            "max": RESTART_MAX})
    _save_state(state)
    return actions


def tick(rows: list[dict] | None = None, state: dict | None = None,
         now: float | None = None) -> dict:
    """One watchdog pass: snapshot → classify → plan → receipts → report."""
    rows = rows if rows is not None else _cim_rows()
    gateways = snapshot(rows)
    actions = recovery_plan(gateways, rows, state=state, now=now)
    now = float(now if now is not None else time.time())
    for a in actions:
        _append_receipt({"ts": now, **a})
    states = classify(gateways, rows)
    return {"gateways": len(gateways),
            "states": {x: sum(1 for g in states if g["state"] == x)
                       for x in ("HEALTHY", "ORPHAN")},
            "actions": actions}


def main(argv: list[str] | None = None) -> int:
    """CLI: one pass; restart actions are executed only within bounds."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--dry-run" in argv:
        rep = tick()
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 0
    rep = tick()
    restarts = [a for a in rep["actions"] if a["kind"] == "restart"]
    if restarts:
        # Restart the gateway with the same python and args; env from .env.
        cmd = [sys.executable, "-X", "utf8",
               str(_OPS / "telegram_center" / "miniapp_gateway.py")]
        try:
            subprocess.Popen(cmd, cwd=str(_OPS),
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            _append_receipt({"ts": time.time(), "kind": "restart_executed"})
        except Exception as exc:  # noqa: BLE001
            _append_receipt({"ts": time.time(), "kind": "restart_failed",
                             "error": type(exc).__name__})
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
