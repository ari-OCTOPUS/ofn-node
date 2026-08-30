"""
control_plane/channel_doctor.py — دکترِ کانال‌ها (Phase 9).

برای هر کانالِ registry چک می‌کند: source هست؟ sink/state هست؟ روی bus
فعالیتی دیده شده؟ تست دارد؟ owner/risk/authority معلوم است؟

خروجی: PASS / WARN / FAIL / UNKNOWN  به‌ازای هر کانال +
گزارش در outputs/control_plane/_reports/channel_doctor.{json,md}

قواعدِ حکم (deterministic):
  • declared status == UNKNOWN  → حکم UNKNOWN (هرگز PASS — silent-pass ممنوع).
  • declared status == MISSING  → حکم FAIL (نبودن را صادقانه گزارش کن).
  • source موجود نیست            → FAIL.
  • state_file غایب / bus ساکت / تستِ اعلام‌شده غایب → WARN.
  • فقط وقتی همه‌چیز هست و declared==CONNECTED → PASS.

نوشتن فقط در دایرکتوریِ گزارشِ خودش — به هیچ storeی دیگری دست نمی‌زند.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from control_plane.registry import Registry, load_registry

SYSTEM_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = SYSTEM_ROOT / "outputs" / "4d_experiments.db"
DEFAULT_REPORT_DIR = SYSTEM_ROOT / "outputs" / "control_plane" / "_reports"


def _bus_count(db: Path, agent_ids: list[str], event_names: list[str]) -> int | None:
    """شمارِ رویدادهای مرتبط با کانال. جدول/DB غایب → None (=UNKNOWN)."""
    if not db.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
        try:
            clauses, params = [], []
            if agent_ids:
                clauses.append(f"agent_id IN ({','.join('?' * len(agent_ids))})")
                params += agent_ids
            if event_names and not agent_ids:
                clauses.append(f"event_name IN ({','.join('?' * len(event_names))})")
                params += event_names
            where = f"WHERE {' OR '.join(clauses)}" if clauses else ""
            row = conn.execute(
                f"SELECT COUNT(*) FROM dashboard_events {where}", params).fetchone()
            return int(row[0])
        finally:
            conn.close()
    except sqlite3.Error:
        return None


def check_channel(ch: dict[str, Any], root: Path, db: Path) -> dict[str, Any]:
    """چکِ یک کانال → dict شامل checks + verdict."""
    # normalize: حکم نباید به حروفِ بزرگ/کوچکِ دست‌نوشته‌ی YAML وابسته باشد.
    declared = str(ch.get("status", "UNKNOWN")).strip().upper()
    VALID = {"CONNECTED", "PARTIAL", "MISSING", "UNKNOWN"}

    # source: اگر شبیه مسیر است، وجودش را بسنج؛ وگرنه n/a
    src = str(ch.get("source", "")).split("::")[0].strip()
    looks_like_path = ("/" in src or src.endswith(".py")) and " " not in src
    source_exists: bool | None = (root / src).exists() if looks_like_path else None

    # state files
    state_files = ch.get("state_files") or []
    missing_state = [f for f in state_files if not (root / f).exists()]
    sinks_ok: bool | None = (not missing_state) if state_files else None

    # bus activity
    agent_ids = ch.get("agent_ids") or []
    event_names = ch.get("event_names") or []
    bus_n: int | None = None
    if agent_ids or event_names:
        bus_n = _bus_count(db, agent_ids, event_names)

    # tests
    tests = ch.get("tests") or []
    missing_tests = [t for t in tests if not (root / t).exists()]
    tests_ok: bool | None = (not missing_tests) if tests else None

    meta_ok = all(ch.get(k) for k in ("risk_tier", "authority"))
    replay_known = str(ch.get("replay", "UNKNOWN")).upper() != "UNKNOWN"

    checks = {
        "source_exists": source_exists,
        "state_files_ok": sinks_ok,
        "missing_state": missing_state,
        "bus_events_seen": bus_n,
        "tests_ok": tests_ok,
        "missing_tests": missing_tests,
        "meta_complete": meta_ok,
        "replay_known": replay_known,
        "declared_status": declared,
    }

    # ── حکم ──
    if declared == "MISSING":
        verdict = "FAIL"
    elif declared not in VALID or declared == "UNKNOWN":
        # UNKNOWN یا هر مقدارِ نامعتبر/تایپی → هرگز PASS (قاعده‌ی طلایی)
        verdict = "UNKNOWN"
    elif source_exists is False:
        verdict = "FAIL"
    else:
        soft_bad = (
            (sinks_ok is False)
            or (bus_n == 0)
            or (tests_ok is False)
            or (not meta_ok)
            or (declared != "CONNECTED")   # فقط CONNECTED می‌تواند PASS شود
            or (not replay_known)
        )
        # PASS فقط با دستِ‌کم یک شاهدِ مثبتِ راستی‌آزمایی‌شده (نه صرفاً وجودِ source):
        has_positive_evidence = (sinks_ok is True) or (tests_ok is True) or \
                                (isinstance(bus_n, int) and bus_n > 0)
        hard_unknown = (source_exists is None and sinks_ok is None
                        and bus_n is None and tests_ok is None)
        if hard_unknown:
            verdict = "UNKNOWN"
        elif soft_bad or not has_positive_evidence:
            verdict = "WARN"
        else:
            verdict = "PASS"

    return {"id": ch.get("id"), "name": ch.get("name"), "verdict": verdict,
            "checks": checks, "notes": ch.get("notes", "")}


def run_doctor(registry_path: str | Path | None = None,
               root: Path | None = None,
               db: Path | None = None,
               report_dir: Path | None = None,
               write_reports: bool = True) -> dict[str, Any]:
    """اجرای کامل دکتر روی همه‌ی کانال‌ها + (اختیاری) نوشتنِ گزارش."""
    root = root or SYSTEM_ROOT
    db = db or DEFAULT_DB
    reg: Registry = load_registry(registry_path) if registry_path else load_registry()

    results = [check_channel(ch, root, db) for ch in reg.channels]
    summary = {"PASS": 0, "WARN": 0, "FAIL": 0, "UNKNOWN": 0}
    for r in results:
        summary[r["verdict"]] = summary.get(r["verdict"], 0) + 1

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "registry": reg.source_path,
        "registry_problems": reg.validate(),
        "summary": summary,
        "channels": results,
    }

    if write_reports:
        rd = report_dir or DEFAULT_REPORT_DIR
        rd.mkdir(parents=True, exist_ok=True)
        (rd / "channel_doctor.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        (rd / "channel_doctor.md").write_text(_render_md(report), encoding="utf-8")
        report["report_json"] = str(rd / "channel_doctor.json")
        report["report_md"] = str(rd / "channel_doctor.md")
    return report


_ICON = {"PASS": "✅", "WARN": "🟡", "FAIL": "🔴", "UNKNOWN": "⚪"}


def _render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Channel Doctor — گزارشِ سلامتِ کانال‌ها",
        f"_تولید: {report['generated_at']} · registry: {report['registry']}_",
        "",
        "| کانال | حکم | source | state | bus | tests | یادداشت |",
        "|---|---|---|---|---|---|---|",
    ]
    def _b(v):  # bool|None → علامت
        return {True: "✓", False: "✗", None: "–"}[v]
    for r in report["channels"]:
        c = r["checks"]
        bus = c["bus_events_seen"]
        lines.append(
            f"| {r['id']} | {_ICON[r['verdict']]} {r['verdict']} | "
            f"{_b(c['source_exists'])} | {_b(c['state_files_ok'])} | "
            f"{bus if bus is not None else '–'} | {_b(c['tests_ok'])} | "
            f"{(r.get('notes') or '')[:60]} |")
    s = report["summary"]
    lines += ["", f"**خلاصه:** ✅ {s['PASS']} · 🟡 {s['WARN']} · "
                  f"🔴 {s['FAIL']} · ⚪ {s['UNKNOWN']}"]
    if report.get("registry_problems"):
        lines += ["", "## مشکلاتِ registry"] + [f"- {p}" for p in report["registry_problems"]]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    rep = run_doctor()
    print(json.dumps(rep["summary"], ensure_ascii=False))
    print("report:", rep.get("report_md", "(نوشته نشد)"))
