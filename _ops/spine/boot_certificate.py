#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""boot_certificate.py — C2-E: شناسنامهٔ تولد (`system.booted` → spine).

RESURRECTION فاز ۱۰: هر بیدارشدن یک رویدادِ durable با زنجیرهٔ `prev_boot_id` —
ارگانیسم سلسله‌مراتبِ تولدهایش را می‌شناسد؛ هویتِ پیوسته، نه personaهای فراموشکار.

قیود:
  - پشتِ OCTOPUS_WIRE_SPINE (flag خاموش → skip، صفر I/O).
  - `flags_hash` فقط **ساختار** را هش می‌کند: بایت‌های flags.cmd (کانفیگِ non-secret 0/1)
    + فقط **نامِ** کلیدهای .env — هرگز هیچ مقداری از .env خوانده/هش/چاپ نمی‌شود.
  - state_checksums: شمارش + آخرین‌شناسه از هر SoT (fail-soft per store).
  - fail-soft کامل: شکستِ شناسنامه هرگز بوت را نمی‌کشد.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _bootstrap() -> None:
    for _p in (str(_HERE), str(_HERE.parent), str(_HERE.parent / "outcomes"),
               str(_HERE.parent / "budget")):
        if _p not in sys.path:
            sys.path.insert(0, _p)


def _flags_hash(ops_dir: Path, env_file: Path) -> str:
    """sha256(بایت‌های flags.cmd + نامِ کلیدهای .env) — ساختار، نه secret."""
    h = hashlib.sha256()
    fc = ops_dir / "OCTOPUS-flags.cmd"
    try:
        h.update(fc.read_bytes() if fc.exists() else b"<no-flags-file>")
    except OSError:
        h.update(b"<flags-unreadable>")
    h.update(b"\x00")
    names = []
    try:
        if env_file.exists():
            for ln in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
                ln = ln.strip()
                if ln and not ln.startswith("#") and "=" in ln:
                    names.append(ln.split("=", 1)[0].strip())   # فقط نام — هرگز مقدار
    except OSError:
        names = ["<env-unreadable>"]
    h.update("\n".join(sorted(names)).encode("utf-8"))
    return h.hexdigest()


def _count_and_last(db: Path, table: str, id_col: str) -> "dict | None":
    if not db.exists():
        return None
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        last = con.execute(
            f"SELECT {id_col} FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
        con.close()
        return {"count": n, "last": (last[0] if last else None)}
    except sqlite3.Error:
        return {"count": None, "last": None}


def _state_checksums(state_dir: Path, ledger_path: "Path | None") -> dict:
    out = {
        "spine": _count_and_last(state_dir / "spine" / "spine.db", "events", "event_id"),
        "outcomes": _count_and_last(state_dir / "outcomes" / "outcomes.db",
                                    "outcomes", "event_id"),
        "memory": _count_and_last(state_dir / "memory" / "memory.db", "memory", "memory_id"),
        "chrono": None, "ledger": None,
    }
    ch = state_dir / "chrono.db"
    if ch.exists():
        try:
            con = sqlite3.connect(f"file:{ch}?mode=ro", uri=True)
            out["chrono"] = {
                "gated_effect": con.execute("SELECT COUNT(*) FROM gated_effect").fetchone()[0],
                "checkpoint": con.execute("SELECT COUNT(*) FROM checkpoint").fetchone()[0],
                "user_version": con.execute("PRAGMA user_version").fetchone()[0]}
            con.close()
        except sqlite3.Error:
            out["chrono"] = {"error": "unreadable"}
    if ledger_path is not None and ledger_path.exists():
        try:
            lines = [ln for ln in ledger_path.read_text(
                encoding="utf-8", errors="replace").splitlines() if ln.strip()]
            out["ledger"] = {
                "count": len(lines),
                "last_sha12": hashlib.sha256(
                    lines[-1].encode("utf-8")).hexdigest()[:12] if lines else None}
        except OSError:
            out["ledger"] = {"error": "unreadable"}
    return out


def _prev_boot(spine) -> "tuple[str | None, str | None]":
    """(prev_boot_id, last_event_recorded_at) از spine — زنجیرهٔ تولد + محاسبهٔ خواب."""
    prev_id = last_at = None
    try:
        rows = spine._conn.execute(   # noqa: SLF001 — projection read
            "SELECT payload_json FROM events WHERE event_type='system.booted' "
            "ORDER BY rowid DESC LIMIT 1").fetchone()
        if rows:
            try:
                prev_id = (json.loads(rows[0] or "{}") or {}).get("boot_id")
            except ValueError:
                prev_id = None
        r2 = spine._conn.execute(   # noqa: SLF001
            "SELECT MAX(recorded_at) FROM events").fetchone()
        last_at = r2[0] if r2 else None
    except sqlite3.Error:
        pass
    return prev_id, last_at


def emit_birth_certificate(*, state_dir=None, ledger_path=None, env_file=None,
                           extras: "dict | None" = None) -> dict:
    """رویدادِ `system.booted` را به spine بزن. خروجی همیشه dict؛ هرگز raise.
    {emitted, boot_id, prev_boot_id, reason?}"""
    _bootstrap()
    try:
        import event_spine as es   # noqa: WPS433
        if not es.flag_on():
            return {"emitted": False, "reason": "flag-off"}
        import opslib   # noqa: WPS433
        sdir = Path(state_dir) if state_dir else Path(opslib.STATE_DIR)
        ops_dir = sdir.parent if sdir.name == "state" else sdir
        envf = Path(env_file) if env_file else (ops_dir.parent / ".env")
        ledp = Path(ledger_path) if ledger_path else None
        if ledp is None:
            try:
                lp = Path(str(opslib.ORG_ROOT)) / "07 - Knowledge" / "genome-system" \
                    / "ledger" / "ledger.jsonl"
                ledp = lp if lp.exists() else None
            except Exception:  # noqa: BLE001
                ledp = None
        spdir = sdir / "spine"
        spdir.mkdir(parents=True, exist_ok=True)
        spine = es.EventSpine(path=spdir / "spine.db")
        prev_id, last_at = _prev_boot(spine)
        now = datetime.now(timezone.utc)
        gap_s = None
        if last_at:
            try:
                t = datetime.fromisoformat(str(last_at))
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                gap_s = max(0.0, (now - t).total_seconds())
            except ValueError:
                gap_s = None
        try:
            halt = "armed" if opslib.halted() else "clear"
        except Exception:  # noqa: BLE001
            halt = "unknown"
        boot_id = uuid.uuid4().hex
        cert = {"event": "system.booted", "boot_id": boot_id,
                "prev_boot_id": prev_id, "booted_at": now.isoformat(),
                "uptime_gap_s": gap_s, "halt_state": halt,
                "flags_hash": _flags_hash(ops_dir, envf),
                "state_checksums": _state_checksums(sdir, ledp),
                **({} if not extras else {"recovery": extras})}
        eid = spine.publish({"event_type": "system.booted", "domain": "system",
                             "correlation_id": f"boot_{boot_id}", "subject": boot_id,
                             "producer": "organism-boot", "trust": "DETERMINISTIC",
                             "payload": cert})
        try:
            spine._conn.close()   # noqa: SLF001
        except Exception:  # noqa: BLE001
            pass
        return {"emitted": bool(eid), "boot_id": boot_id, "prev_boot_id": prev_id,
                "event_id": eid, "uptime_gap_s": gap_s}
    except Exception as e:  # noqa: BLE001 — شناسنامه هرگز بوت را نمی‌کشد
        return {"emitted": False, "reason": f"error: {type(e).__name__}"}
