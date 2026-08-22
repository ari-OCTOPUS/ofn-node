#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed Telegram poller uniqueness probe for doctor / EveLab.

Asserts the continuous multi-agent live invariant:
  - exactly 1 telegram_center/center.py PID (or injected center_pids)
  - exactly 1 ACTIVE row in state/telegram/poll-lease.sqlite3
  - exactly 1 non-stale tg-poller-*.lock (poller_id == center-canonical by default)
  - lease owner_pid + lock pid agree with the single center PID

Dry-run / fixture friendly: never sends Telegram, never restarts center,
never mutates live vault when only reading. seed_uniqueness_fixture() writes
only under an explicit state_dir (tests / lab_call_doctor_check dry-run).
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
_DEFAULT_LOCK_DIR = _OPS / "state" / "locks"
_EXPECTED_POLLER_ID = "center-canonical"
_CENTER_MARKERS = ("telegram_center\\center.py", "telegram_center/center.py", "center.py")


def _state_root(state_dir=None) -> Path:
    if state_dir is not None:
        return Path(state_dir)
    configured = str(os.environ.get("OCTOPUS_STATE_DIR", "") or "").strip()
    if configured:
        return Path(configured)
    return _OPS / "state"


def _lock_dir(state_dir=None) -> Path:
    # tg_poller_lease.LOCK_DIR is always _ops/state/locks (not OCTOPUS_STATE_DIR).
    # Fixtures pass explicit state_dir → use state_dir/locks; live probe uses default.
    if state_dir is not None:
        return Path(state_dir) / "locks"
    return _DEFAULT_LOCK_DIR


def _lease_db(state_dir=None) -> Path:
    return _state_root(state_dir) / "telegram" / "poll-lease.sqlite3"


def _pid_alive(pid: int) -> bool:
    """Best-effort liveness. On Windows os.kill(pid, 0) is unreliable (WinError 87)."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            k = ctypes.windll.kernel32  # type: ignore[attr-defined]
            # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = k.OpenProcess(0x1000, False, int(pid))
            if h:
                k.CloseHandle(h)
                return True
            # fallback: GetExitCodeProcess via SYNCHRONIZE|QUERY
            h = k.OpenProcess(0x100000 | 0x0400, False, int(pid))
            if not h:
                return False
            try:
                code = ctypes.c_ulong()
                if k.GetExitCodeProcess(h, ctypes.byref(code)):
                    return int(code.value) == 259  # STILL_ACTIVE
                return False
            finally:
                k.CloseHandle(h)
        except Exception:  # noqa: BLE001
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def list_center_pids() -> list[int]:
    """Best-effort live scan for telegram_center/center.py. Fail-soft → []."""
    pids: list[int] = []
    if sys.platform == "win32":
        try:
            ps = (
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                "Where-Object { $_.CommandLine -and ("
                "$_.CommandLine -like '*telegram_center*center.py*' -or "
                "$_.CommandLine -like '*telegram_center\\center.py*'"
                ") } | Select-Object -ExpandProperty ProcessId"
            )
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=20,
            )
            for line in (r.stdout or "").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    pids.append(int(line))
                except ValueError:
                    continue
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
    # de-dupe preserve order
    seen: set[int] = set()
    out: list[int] = []
    for p in pids:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def list_active_leases(state_dir=None, *, now: float | None = None) -> list[dict[str, Any]]:
    """Read ACTIVE lease rows. Missing DB → [] (caller fail-closes on count)."""
    db = _lease_db(state_dir)
    if not db.is_file():
        return []
    now = time.time() if now is None else float(now)
    rows: list[dict[str, Any]] = []
    con: sqlite3.Connection | None = None
    try:
        con = sqlite3.connect(str(db), timeout=1.0)
        con.row_factory = sqlite3.Row
        try:
            cur = con.execute(
                "SELECT token_digest, owner_pid, owner_boot_id, state, "
                "lease_until, heartbeat_at, generation "
                "FROM lease WHERE UPPER(state)='ACTIVE'"
            )
        except sqlite3.Error:
            return []
        for r in cur.fetchall():
            lease_until = float(r["lease_until"] or 0.0)
            rows.append({
                "token_digest": str(r["token_digest"] or "")[:16] + "…",
                "token_digest_prefix": str(r["token_digest"] or "")[:12],
                "owner_pid": int(r["owner_pid"]),
                "owner_boot_id": str(r["owner_boot_id"] or "")[:64],
                "state": str(r["state"] or ""),
                "lease_until": lease_until,
                "lease_remaining_s": round(lease_until - now, 1),
                "heartbeat_at": float(r["heartbeat_at"] or 0.0),
                "generation": int(r["generation"] or 0),
                "expired": lease_until < now,
            })
    except (OSError, sqlite3.Error, ValueError, TypeError):
        return []
    finally:
        if con is not None:
            con.close()
    return rows


def list_tg_poller_locks(
    state_dir=None,
    *,
    require_alive: bool = True,
    expected_poller_id: str = _EXPECTED_POLLER_ID,
) -> list[dict[str, Any]]:
    """Non-stale tg-poller-*.lock records under locks dir."""
    ld = _lock_dir(state_dir)
    if not ld.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(ld.glob("tg-poller-*.lock")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
        if not isinstance(rec, dict):
            continue
        try:
            pid = int(rec.get("pid", -1))
        except (TypeError, ValueError):
            continue
        alive = _pid_alive(pid) if require_alive else True
        if require_alive and not alive:
            continue
        out.append({
            "path": path.name,
            "schema": rec.get("schema"),
            "poller_id": rec.get("poller_id"),
            "pid": pid,
            "token_fp": rec.get("token_fp"),
            "acquired_at": rec.get("acquired_at"),
            "alive": alive,
            "expected_poller_id_match": rec.get("poller_id") == expected_poller_id,
        })
    return out


def seed_uniqueness_fixture(
    state_dir,
    *,
    center_pid: int = 424242,
    poller_id: str = _EXPECTED_POLLER_ID,
    token_fp: str = "deadbeefcafe",
    token_digest: str | None = None,
    now: float | None = None,
    extra_active_leases: int = 0,
    extra_locks: int = 0,
) -> dict[str, Any]:
    """Write a minimal 1/1/1 (or deliberately broken) fixture under state_dir."""
    root = Path(state_dir)
    locks = root / "locks"
    tg = root / "telegram"
    locks.mkdir(parents=True, exist_ok=True)
    tg.mkdir(parents=True, exist_ok=True)
    now = time.time() if now is None else float(now)
    digest = token_digest or ("fixture" + ("0" * 56))[:64]

    db = tg / "poll-lease.sqlite3"
    con = sqlite3.connect(str(db))
    try:
        con.execute(
            "CREATE TABLE IF NOT EXISTS lease("
            "token_digest TEXT PRIMARY KEY, owner_pid INTEGER NOT NULL, "
            "owner_boot_id TEXT NOT NULL, acquired_at REAL NOT NULL, "
            "heartbeat_at REAL NOT NULL, lease_until REAL NOT NULL, "
            "state TEXT NOT NULL DEFAULT 'ACTIVE', "
            "fail_count INTEGER NOT NULL DEFAULT 0, "
            "cooldown_until REAL NOT NULL DEFAULT 0, "
            "generation INTEGER NOT NULL DEFAULT 1, "
            "owner_instance TEXT, host_boot_digest TEXT, code_head TEXT, "
            "request_deadline REAL, last_reason TEXT)"
        )
        con.execute("DELETE FROM lease")
        rows = [(digest, center_pid)]
        for i in range(extra_active_leases):
            rows.append(((f"extra{i:02d}" + ("x" * 56))[:64], center_pid + 1 + i))
        for dig, pid in rows:
            con.execute(
                "INSERT INTO lease(token_digest,owner_pid,owner_boot_id,"
                "acquired_at,heartbeat_at,lease_until,state,fail_count,"
                "cooldown_until,generation) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (dig, int(pid), f"{pid}:fixture", now, now, now + 90.0,
                 "ACTIVE", 0, 0.0, 1),
            )
        con.commit()
    finally:
        con.close()

    # clear prior fixture locks
    for old in locks.glob("tg-poller-*.lock"):
        try:
            old.unlink()
        except OSError:
            pass
    lock_specs = [(token_fp, center_pid, poller_id)]
    for i in range(extra_locks):
        lock_specs.append((f"xtra{i:08d}", center_pid + 10 + i, f"extra-{i}"))
    for fp, pid, pol in lock_specs:
        payload = {
            "schema": "tg-poller-lease/1",
            "poller_id": pol,
            "pid": int(pid),
            "token_fp": fp,
            "acquired_at": now,
        }
        (locks / f"tg-poller-{fp}.lock").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    return {
        "state_dir": str(root),
        "center_pid": int(center_pid),
        "lease_db": str(db),
        "lock_dir": str(locks),
        "active_leases_seeded": 1 + extra_active_leases,
        "locks_seeded": 1 + extra_locks,
    }



def record_uniqueness_receipt(
    result: dict[str, Any],
    *,
    state_dir=None,
    beat: int = 0,
    source: str = "doctor_uniqueness_beat",
    dry_run: bool = True,
) -> dict[str, Any]:
    """Persist RO uniqueness receipt under state/doctor/. Never Telegram."""
    root = _state_root(state_dir)
    doc = root / "doctor"
    doc.mkdir(parents=True, exist_ok=True)
    now = time.time()
    try:
        from datetime import datetime
        try:
            from zoneinfo import ZoneInfo
            local = datetime.now(ZoneInfo("Australia/Sydney")).isoformat(timespec="seconds")
        except Exception:  # noqa: BLE001
            local = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    except Exception:  # noqa: BLE001
        local = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rec = {
        "schema": "poller-uniqueness-receipt/1",
        "source": str(source),
        "beat": int(beat or 0),
        "checked_at_unix": now,
        "checked_at_local": local,
        "dry_run": bool(dry_run),
        "live_send": False,
        "ok": bool((result or {}).get("ok")),
        "fail_closed": True,
        "checks": (result or {}).get("checks"),
        "reasons": list((result or {}).get("reasons") or []),
        "center_pid_count": (result or {}).get("center_pid_count"),
        "active_lease_count": (result or {}).get("active_lease_count"),
        "tg_poller_lock_count": (result or {}).get("tg_poller_lock_count"),
        "center_pids": (result or {}).get("center_pids"),
        "paths": (result or {}).get("paths"),
        "probe": (result or {}).get("probe") or "poller-uniqueness/1",
    }
    latest = doc / "poller-uniqueness-latest.json"
    tmp = latest.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, latest)
    log = doc / "poller-uniqueness.jsonl"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {
        "path": str(latest),
        "jsonl": str(log),
        "ok": rec["ok"],
        "live_send": False,
        "receipt": rec,
    }


def check_poller_uniqueness(
    *,
    state_dir=None,
    center_pids: list[int] | None = None,
    expected_poller_id: str = _EXPECTED_POLLER_ID,
    require_lock_pid_alive: bool = True,
    now: float | None = None,
    scan_live_pids: bool = True,
) -> dict[str, Any]:
    """Fail-closed uniqueness probe. Returns structured ok + reasons."""
    now = time.time() if now is None else float(now)
    reasons: list[str] = []

    if center_pids is None:
        if scan_live_pids:
            center_pids = list_center_pids()
        else:
            center_pids = []
            reasons.append("center_pids_missing")
    else:
        center_pids = [int(p) for p in center_pids]

    leases = list_active_leases(state_dir, now=now)
    # For uniqueness, count ACTIVE rows (including expired ACTIVE — still "claimed")
    active_leases = leases
    locks = list_tg_poller_locks(
        state_dir,
        require_alive=require_lock_pid_alive,
        expected_poller_id=expected_poller_id,
    )

    one_center = len(center_pids) == 1
    one_lease = len(active_leases) == 1
    one_lock = len(locks) == 1
    if not one_center:
        reasons.append(f"center_pid_count={len(center_pids)} expected=1")
    if not one_lease:
        reasons.append(f"active_lease_count={len(active_leases)} expected=1")
    if not one_lock:
        reasons.append(f"tg_poller_lock_count={len(locks)} expected=1")

    pids_agree = False
    if one_center and one_lease and one_lock:
        cpid = center_pids[0]
        lpid = int(active_leases[0]["owner_pid"])
        kpid = int(locks[0]["pid"])
        poller_ok = locks[0].get("poller_id") == expected_poller_id
        pids_agree = (cpid == lpid == kpid) and poller_ok
        if cpid != lpid:
            reasons.append(f"lease_owner_pid={lpid} != center_pid={cpid}")
        if cpid != kpid:
            reasons.append(f"lock_pid={kpid} != center_pid={cpid}")
        if not poller_ok:
            reasons.append(
                f"poller_id={locks[0].get('poller_id')!r} expected={expected_poller_id!r}"
            )
    else:
        reasons.append("pids_agree_skipped")

    ok = one_center and one_lease and one_lock and pids_agree and not reasons
    # rebuild ok strictly from boolean gates (reasons may still list detail)
    ok = bool(one_center and one_lease and one_lock and pids_agree)

    return {
        "ok": ok,
        "fail_closed": True,
        "dry_run_safe": True,
        "live_send": False,
        "center_pids": center_pids,
        "center_pid_count": len(center_pids),
        "active_leases": active_leases,
        "active_lease_count": len(active_leases),
        "tg_poller_locks": locks,
        "tg_poller_lock_count": len(locks),
        "checks": {
            "one_center_pid": one_center,
            "one_active_lease": one_lease,
            "one_tg_poller_lock": one_lock,
            "pids_agree": pids_agree,
        },
        "reasons": reasons if not ok else [],
        "paths": {
            "state_dir": str(_state_root(state_dir)),
            "lease_db": str(_lease_db(state_dir)),
            "lock_dir": str(_lock_dir(state_dir)),
        },
        "probe": "poller-uniqueness/1",
    }


__all__ = [
    "check_poller_uniqueness",
    "seed_uniqueness_fixture",
    "list_center_pids",
    "list_active_leases",
    "list_tg_poller_locks",
    "record_uniqueness_receipt",
]
