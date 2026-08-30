"""
control_plane/snapshot.py — جمع‌آورِ وضعیت، ۱۰۰٪ read-only.

اصل: «سطحِ مشاهده هرگز در storeی مشاهده‌شده نمی‌نویسد.»
  • فقط فایل/SQLite می‌خوانَد (SELECT)؛ هیچ CREATE/INSERT/UPDATE، هیچ import
    از brain/* (تا حتی DDLِ idempotent هم رخ ندهد).
  • هر جمع‌آور اگر منبع نبود/خراب بود → status="UNKNOWN" برمی‌گرداند؛
    exception نمی‌ترکد و silent-pass هم نمی‌کند.
  • secrets: هیچ فایلی خارج از outputs/ و هیچ متغیرِ محرمانه‌ای خوانده نمی‌شود.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from control_plane.flags import all_flags, governance_mode

SYSTEM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = SYSTEM_ROOT / "outputs"

_UNKNOWN = "UNKNOWN"


def _read_json(path: Path) -> dict | None:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def _age_seconds(iso_ts: str) -> float | None:
    try:
        return (datetime.now() - datetime.fromisoformat(iso_ts)).total_seconds()
    except Exception:
        return None


# ── daemon ───────────────────────────────────────────────────────────────
def daemon_status(out: Path = DEFAULT_OUT) -> dict[str, Any]:
    """وضعیتِ daemon از heartbeat فایل + فایل‌های pause/stop (قراردادِ موجود)."""
    state = _read_json(out / "daemon_state.json")
    pause = (out / "daemon.pause").exists()
    stop = (out / "daemon.stop").exists()
    if not state:
        return {"status": _UNKNOWN, "reason": "daemon_state.json نیست/ناخوانا",
                "pause_file": pause, "stop_file": stop}

    try:
        tick_s = max(1.0, float(os.getenv("DAEMON_TICK_SECONDS", "30")))
    except ValueError:
        tick_s = 30.0
    last_tick = state.get("last_tick_at", "")
    resumed = state.get("resumed_at", "")
    started = state.get("started_at", "")
    stopped = state.get("stopped_at", "")
    age = _age_seconds(last_tick) if last_tick else None

    # «سیگنالِ زنده‌بودن» = تازه‌ترینِ heartbeat/resumed/started. رشته‌های ISO با
    # فرمتِ یکسان (timespec=seconds) قابلِ مقایسه‌ی لغوی‌اند.
    life_signals = [t for t in (last_tick, resumed, started) if t]
    freshest = max(life_signals) if life_signals else ""
    age_fresh = _age_seconds(freshest) if freshest else None
    # daemon فقط وقتی «متوقف» است که بعد از آخرین stop، هیچ سیگنالِ زنده‌ی جدیدی نباشد.
    # (رفعِ باگ: daemon هرگز stopped_at را روی restart پاک نمی‌کند؛ resumed/started
    #  نشان می‌دهند که دوباره بالا آمده — پس STOPPED نگوییم.)
    alive_after_stop = (
        (resumed and resumed >= stopped)
        or (started and started >= stopped)
        or (last_tick and last_tick > stopped)
    )
    if stopped and not alive_after_stop:
        verdict = "STOPPED"
    elif age_fresh is not None and age_fresh <= 3 * tick_s:
        # heartbeat تازه، یا (در پنجره‌ی restart) resumed/started تازه ولی هنوز
        # heartbeatِ tick نیامده — در هر دو حالت daemon زنده است.
        verdict = "PAUSED" if pause else "RUNNING"
    elif age_fresh is not None:
        verdict = "STALE"
    else:
        verdict = _UNKNOWN

    return {
        "status": verdict,
        "pause_file": pause,
        "stop_file": stop,
        "pid": state.get("pid"),
        "last_tick_at": last_tick,
        "stopped_at": stopped,
        "heartbeat_age_s": round(age, 1) if age is not None else None,
        "total_ticks": state.get("total_ticks"),
        "errors_this_run": state.get("errors_this_run"),
        "halted_at": state.get("halted_at", ""),
        "generation": state.get("generation"),
    }


# ── budget ───────────────────────────────────────────────────────────────
def budget_status(out: Path = DEFAULT_OUT) -> dict[str, Any]:
    data = _read_json(out / "llm_budget.json")
    try:
        cap = max(0, int(os.getenv("LLM_DAILY_CALL_CAP", "1000")))
    except ValueError:
        cap = 1000
    if not data:
        return {"status": _UNKNOWN, "cap": cap}
    today = datetime.now().strftime("%Y-%m-%d")
    calls = data.get("calls", {}) if data.get("date") == today else {}
    # منبعِ حقیقت = brain/budget.CLOUD_PROVIDERS (whitelist)، نه blacklistِ «!=ollama».
    # اگر روزی provider محلیِ جدیدی زیرِ کلیدِ دیگری ثبت شود، این whitelist اشتباه
    # نمی‌شمارد. (brain/budget.py:22 → frozenset({"fugu","glm","langchain"}))
    CLOUD_PROVIDERS = {"fugu", "glm", "langchain"}
    cloud = sum(int(v) for k, v in calls.items() if k in CLOUD_PROVIDERS)
    return {"status": "OK", "date": data.get("date"), "cap": cap,
            "cloud_calls": cloud, "remaining": max(0, cap - cloud),
            "by_provider": calls}


# ── event bus (فقط SELECT) ───────────────────────────────────────────────
def _bus_query(db: Path, sql: str, params: tuple = ()) -> list | None:
    """SELECT امن؛ جدول/فایل غایب → None (نه exception، نه ساختِ جدول)."""
    if not db.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        try:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.execute(sql, params).fetchall()]
        finally:
            conn.close()
    except sqlite3.Error:
        return None


def events_summary(db: Path | None = None, recent: int = 15) -> dict[str, Any]:
    db = db or (DEFAULT_OUT / "4d_experiments.db")
    counts = _bus_query(db, "SELECT event_name, COUNT(*) AS n FROM dashboard_events GROUP BY event_name")
    if counts is None:
        return {"status": _UNKNOWN, "reason": "bus/جدول در دسترس نیست"}
    by_name = {r["event_name"]: r["n"] for r in counts}
    pending = _bus_query(db, "SELECT COUNT(*) AS n FROM dashboard_events WHERE approval_state='pending'")
    last = _bus_query(db, "SELECT * FROM dashboard_events ORDER BY id DESC LIMIT ?", (recent,))
    return {
        "status": "OK",
        "total": sum(by_name.values()),
        "by_name": by_name,
        "errors": by_name.get("task.failed", 0),
        "blocked": by_name.get("task.blocked", 0),
        "pending_approvals": (pending[0]["n"] if pending else 0),
        "recent": last or [],
    }


def workspace_status(db: Path | None = None, window: int = 80) -> dict[str, Any]:
    """بازپیاده‌سازیِ خواندنیِ فرمول‌های brain/workspace.py (مرجع همان‌جاست).

    عمداً import نمی‌کنیم تا مسیرِ observe هیچ DDLی (حتی idempotent) اجرا نکند.
    """
    db = db or (DEFAULT_OUT / "4d_experiments.db")
    rows = _bus_query(db, "SELECT trace_id, agent_id, status, id FROM dashboard_events "
                          "ORDER BY id DESC LIMIT ?", (window,))
    if rows is None:
        return {"status": _UNKNOWN}
    if not rows:
        return {"status": "OK", "mean_ignition": 0.0, "max_ignition": 0,
                "broadcast_width": 0, "coherence": 0.0, "ignition_rate": 0.0, "n": 0}
    traces: dict[str, set] = {}
    for r in rows:
        tid = r.get("trace_id") or f"_{r.get('id')}"
        traces.setdefault(tid, set()).add(r.get("agent_id") or "?")
    ignitions = [len(a) for a in traces.values()]
    ignited = sum(1 for x in ignitions if x >= 2)
    ok = sum(1 for r in rows if r.get("status") == "ok")
    return {
        "status": "OK",
        "mean_ignition": round(sum(ignitions) / max(len(ignitions), 1), 2),
        "max_ignition": max(ignitions),
        "broadcast_width": len({r.get("agent_id") for r in rows}),
        "coherence": round(ok / max(len(rows), 1), 2),
        "ignition_rate": round(ignited / max(len(ignitions), 1), 2),
        "n": len(rows),
    }


# ── approvals (mirror فقط‌خواندنی) ──────────────────────────────────────
def approvals_status(out: Path = DEFAULT_OUT, db: Path | None = None) -> dict[str, Any]:
    """صفِ self_code (خواندنِ مستقیمِ meta.json) + approvalهای معلقِ bus."""
    pdir = out / "self_code_proposals"
    pending: list[dict] = []
    counts: dict[str, int] = {}
    if pdir.exists():
        for meta_file in sorted(pdir.glob("*/meta.json"), reverse=True):
            try:
                meta = json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            st_ = meta.get("status", "?")
            counts[st_] = counts.get(st_, 0) + 1
            if st_ == "pending_approval":
                pending.append({k: meta.get(k) for k in
                                ("id", "target", "goal", "created_at", "proposer")})
    ev = events_summary(db)
    return {
        "status": "OK" if pdir.exists() else _UNKNOWN,
        "self_code_pending": pending,
        "self_code_counts": counts,
        "bus_pending_approvals": ev.get("pending_approvals", _UNKNOWN),
        "note": "apply فقط از مسیرِ امنِ موجود (داشبورد/تلگرام) — این‌جا فقط visibility",
    }


# ── evolution / SOG ──────────────────────────────────────────────────────
def evolution_status(out: Path = DEFAULT_OUT) -> dict[str, Any]:
    se = out / "self_evolved"
    strategy = _read_json(se / "strategy.json")
    conclusions = _read_json(se / "conclusions.json")
    frontier = _read_json(se / "frontier.json")
    frontier_cells = None
    if isinstance(frontier, dict):
        cells = frontier.get("cells", frontier)
        frontier_cells = len(cells) if isinstance(cells, (dict, list)) else None
    return {
        "status": "OK" if (strategy or conclusions or frontier) else _UNKNOWN,
        "generation": (strategy or {}).get("_generation"),
        "fitness": (strategy or {}).get("_fitness"),
        "anchors_ok": (conclusions or {}).get("anchors_ok", _UNKNOWN),
        "n_cells": (conclusions or {}).get("n_cells"),
        "detection_rate": (conclusions or {}).get("detection_rate"),
        "frontier_cells": frontier_cells,
        "invariant_note": "اتحاد 0.135073 — visible, not mutable (core/ TCB)",
    }


# ── notify / telegram ────────────────────────────────────────────────────
def notify_status(out: Path = DEFAULT_OUT, tail: int = 5) -> dict[str, Any]:
    jl = out / "decision_packets.jsonl"
    if not jl.exists():
        return {"status": _UNKNOWN, "reason": "decision_packets.jsonl نیست"}
    packets: list[dict] = []
    try:
        lines = jl.read_text(encoding="utf-8", errors="replace").strip().splitlines()
        for line in lines[-tail:]:
            try:
                packets.append(json.loads(line))
            except Exception:
                continue
        delivered_last = (packets[-1].get("delivered", "") if packets else "").strip()
        # فقط «telegram» (تحویلِ موفق در brain/notify) یعنی واقعاً متصل. هر
        # «queued (...)» — چه not-configured، چه خطای شبکه/HTTP — یعنی تحویل نشده.
        telegram_delivering = delivered_last == "telegram"
        return {"status": "OK", "total_packets": len(lines),
                "recent": packets,
                "telegram_configured": telegram_delivering,
                "telegram_delivering": telegram_delivering,
                "last_delivered": delivered_last}
    except Exception as e:
        return {"status": _UNKNOWN, "reason": f"{type(e).__name__}"}


# ── memory ───────────────────────────────────────────────────────────────
def _dir_size_mb(p: Path) -> float | None:
    try:
        if not p.exists():
            return None
        total = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return round(total / 1_048_576, 1)
    except Exception:
        return None


def memory_status(out: Path = DEFAULT_OUT) -> dict[str, Any]:
    db = out / "4d_experiments.db"
    counts = {}
    for table in ("experiments", "hypotheses", "reflections"):
        rows = _bus_query(db, f"SELECT COUNT(*) AS n FROM {table}")  # نامِ ثابتِ schema
        counts[table] = rows[0]["n"] if rows else _UNKNOWN
    return {
        "status": "OK" if db.exists() else _UNKNOWN,
        "db_size_mb": round(db.stat().st_size / 1_048_576, 1) if db.exists() else None,
        "chroma_size_mb": _dir_size_mb(out / "chroma_db"),
        "counts": counts,
    }


# ── supervisor (ترمیمِ خود — v5) ─────────────────────────────────────────
def supervisor_status(out: Path = DEFAULT_OUT) -> dict[str, Any]:
    """heartbeat خودِ supervisor — فقط خواندن از store خودش."""
    data = _read_json(out / "control_plane" / "supervisor_state.json")
    if not data:
        return {"status": _UNKNOWN, "reason": "supervisor هنوز اجرا نشده"}
    age = _age_seconds(data.get("last_tick_at", ""))
    status = "RUNNING" if (age is not None and age <= 120) else "STALE"
    return {"status": status,
            "heartbeat_age_s": round(age, 1) if age is not None else None,
            "flag_live": data.get("flag_live"),
            "children": data.get("children", {})}


# ── تجمیع ────────────────────────────────────────────────────────────────
def collect_status(out: Path | None = None, db: Path | None = None) -> dict[str, Any]:
    """عکسِ کاملِ یک‌نگاهی برای UI/گزارش. فقط می‌خوانَد."""
    out = out or DEFAULT_OUT
    db = db or (out / "4d_experiments.db")
    return {
        "schema_version": 1,
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "governance_mode": governance_mode(),
        "flags": all_flags(),
        "daemon": daemon_status(out),
        "budget": budget_status(out),
        "events": events_summary(db),
        "workspace": workspace_status(db),
        "approvals": approvals_status(out, db),
        "evolution": evolution_status(out),
        "notify": notify_status(out),
        "memory": memory_status(out),
        "supervisor": supervisor_status(out),
    }
