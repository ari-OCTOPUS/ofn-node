#!/usr/bin/env python3
"""
fitness.py — STAGE 3 پک (نیمهٔ سنجش): fitness واقعی فقط از تجربه‌های تأییدشدهٔ انسانی.

قفل ضد reward-hacking (تعریف قفل‌شدهٔ پک):
  «پذیرش» یک cell فقط از رویدادهای approve-first صف control-brain شمرده می‌شود:
    منبع اول:  logs/outbox.jsonl (append-only؛ فقط بعد از کلیک انسانی نوشته می‌شود)
    تطبیق با:  جدول outbox در core.db (status ∈ sent/rejected/failed + resolved_ts)
  ⚠ نکتهٔ verify‌شده: status ی «approved» وجود ندارد — تأیید یعنی status='sent'.
  اختلاف jsonl↔db بیش از تلورانس = مشکوک به دستکاری → cell از fitness حذف + alert.
  رویدادهای EXPERIENCE خودثبت‌شدهٔ ledger هرگز پذیرش شمرده نمی‌شوند (survive ≠ تأیید).

فرمول (وزن‌ها فقط از budgets.yaml — I6):
  fitness(cell) = w1·VALUE + w2·URGENCY + w3·EFFICIENCY + w4·HUMAN_PRIORITY − w5·WASTE
  VALUE      = نرخ پذیرش انسانی (sent/(sent+rejected)) — پروکسی نرمال ارزش محقق
  EFFICIENCY = خروجی مفید (sent) بر ۱k توکن نسبت به baseline خودِ همان cell
  WASTE      = failed + rejected + رویدادهای متر صفر مشکوک

قید صریح (verdict جلسه ۱۶): fitness عددی تا ~۴ هفته دادهٔ ledger فقط سایه —
خروجی این ماژول تا آن موقع authoritative:false حمل می‌کند و هیچ مصرف‌کننده‌ای
حق تصمیم زنده بر اساسش ندارد.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import opslib  # noqa: E402

TAMPER_TOLERANCE = 0.10          # اختلاف نسبی شمارش jsonl↔db بیش از این = integrity alert
AUTHORITATIVE_AFTER_DAYS = 28    # ~۴ هفته دادهٔ EXPERIENCE (verdict جلسه ۱۶)
HISTORY = opslib.STATE_DIR / "fitness-history.json"


def _read_outbox_jsonl() -> dict[str, dict[str, int]]:
    """رویدادهای انسانی-تأییدشده از logs/outbox.jsonl → per-business شمارش وضعیت‌ها."""
    path = opslib.BRAIN_DIR / "logs" / "outbox.jsonl"
    out: dict[str, dict[str, int]] = {}
    if not path.exists():
        return out
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            status = ev.get("event") or ev.get("status") or ""
            if status not in ("sent", "rejected", "failed"):
                continue
            biz = (ev.get("business") or "unknown").lower()
            out.setdefault(biz, {"sent": 0, "rejected": 0, "failed": 0})
            out[biz][status] += 1
    return out


def _read_outbox_db() -> dict[str, dict[str, int]]:
    """تطبیق: همان شمارش از جدول outbox در core.db (فقط‌خواندنی)."""
    out: dict[str, dict[str, int]] = {}
    db = opslib.BRAIN_DIR / "core.db"
    if not db.exists():
        return out
    uri = "file:///" + quote(str(db.resolve()).replace("\\", "/")) + "?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True, timeout=5)
        rows = con.execute(
            "SELECT business, status, COUNT(*) FROM outbox "
            "WHERE status IN ('sent','rejected','failed') GROUP BY business, status").fetchall()
        con.close()
    except sqlite3.Error as e:
        opslib.alert([f"fitness: outbox db read failed: {e}"])
        return out
    for biz, status, n in rows:
        b = (biz or "unknown").lower()
        out.setdefault(b, {"sent": 0, "rejected": 0, "failed": 0})
        out[b][status] = n
    return out


def _tamper_check(jl: dict, db: dict) -> list[str]:
    """اختلاف دو منبع = مشکوک به دستکاری (تنها راه صادق نگه‌داشتن σ)."""
    alerts = []
    for biz in set(jl) | set(db):
        a, b = jl.get(biz, {}), db.get(biz, {})
        for st in ("sent", "rejected"):
            x, y = a.get(st, 0), b.get(st, 0)
            if max(x, y) >= 5 and abs(x - y) / max(x, y) > TAMPER_TOLERANCE:
                alerts.append(f"integrity: {biz}.{st} jsonl={x} db={y} — cell از fitness حذف شد")
    return alerts


def _experience_span_days() -> int:
    """طول بازهٔ دادهٔ EXPERIENCE در ledger ژنوم (برای گیت authoritative)."""
    path = opslib.GENOME_DIR / "ledger" / "ledger.jsonl"
    if not path.exists():
        return 0
    first = last = None
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            if rec.get("type") == "NOTE" and (rec.get("payload") or {}).get("subtype") == "EXPERIENCE":
                ts = (rec.get("ts") or "")[:10]
                if ts:
                    first = first or ts
                    last = ts
    if not first:
        return 0
    return (dt.date.fromisoformat(last) - dt.date.fromisoformat(first)).days


def _efficiency(biz: str, sent: int, tokens: int, history: dict) -> float:
    """sent بر ۱k توکن، نسبت به baseline خودِ cell (رقابت با تاریخ خودش، بعد با peerها)."""
    if tokens <= 0:
        return 0.5
    rate = sent / (tokens / 1000.0)
    base = history.get(biz, {}).get("eff_baseline")
    if not base:
        return 0.5   # baseline هنوز شکل نگرفته — خنثی
    return max(0.0, min(1.0, 0.5 * rate / base))


def compute(write: bool = True) -> dict:
    b = opslib.load_budgets()
    weights = b["global"].get("weights", {})
    jl, db = _read_outbox_jsonl(), _read_outbox_db()
    tamper = _tamper_check(jl, db)
    tampered = {a.split(":")[1].strip().split(".")[0] for a in tamper} if tamper else set()
    if tamper:
        opslib.alert(tamper)

    # توکن مصرفی per-business از جدول usage (برای EFFICIENCY)
    tokens: dict[str, int] = {}
    dbf = opslib.BRAIN_DIR / "core.db"
    if dbf.exists():
        try:
            uri = "file:///" + quote(str(dbf.resolve()).replace("\\", "/")) + "?mode=ro"
            con = sqlite3.connect(uri, uri=True, timeout=5)
            for biz, t in con.execute(
                    "SELECT business, SUM(tokens_in)+SUM(tokens_out) FROM usage GROUP BY business"):
                tokens[(biz or "unknown").lower()] = int(t or 0)
            con.close()
        except sqlite3.Error:
            pass

    try:
        history = json.loads(HISTORY.read_text("utf-8")) if HISTORY.exists() else {}
    except (OSError, ValueError):
        history = {}

    span = _experience_span_days()
    cells = {}
    for biz in sorted(set(jl) | set(db)):
        if biz in tampered:
            cells[biz] = {"excluded": True, "reason": "integrity-mismatch"}
            continue
        src = jl.get(biz) or db.get(biz) or {}
        sent, rejected, failed = src.get("sent", 0), src.get("rejected", 0), src.get("failed", 0)
        judged = sent + rejected
        acceptance = (sent / judged) if judged else None
        value = acceptance if acceptance is not None else 0.0
        eff = _efficiency(biz, sent, tokens.get(biz, 0), history)
        waste = min(1.0, (failed + rejected) / max(1, judged + failed))
        human = 0.5   # cellهای بیزنسی؛ ضریب انسانی per-organ در governor اعمال می‌شود
        fit = (weights.get("value", .3) * value + weights.get("urgency", .25) * 0.0
               + weights.get("efficiency", .2) * eff + weights.get("human", .2) * human
               - weights.get("waste", .05) * waste)
        cells[biz] = {
            "sent": sent, "rejected": rejected, "failed": failed,
            "acceptance_rate": round(acceptance, 4) if acceptance is not None else None,
            "judged": judged, "tokens": tokens.get(biz, 0),
            "efficiency": round(eff, 4), "waste": round(waste, 4),
            "fitness": round(fit, 4),
        }
        # baseline شخصی برای epoch بعد
        if tokens.get(biz, 0) > 0:
            history.setdefault(biz, {})["eff_baseline"] = max(
                1e-9, sent / (tokens[biz] / 1000.0))

    # اتصالِ attribution (Track B): فقط CONFIRMED/ATTRIBUTED واردِ fitness می‌شود (ناوردی: هرگز زیرِ CONFIRMED).
    # افزایشی و شادو — فرمولِ وزنیِ بالا دست‌نخورده؛ revenue-fitnessِ کامل هنوز شادو (طرحِ MONEY-ATTRIBUTION).
    try:
        import attribution
        attr = attribution.confirmed_revenue()
    except Exception as e:  # noqa: BLE001 — مشاهده fail-soft است (خرج جای دیگر گیت می‌شود)
        attr = {"by_cell": {}, "attribution_coverage": None, "claimed": 0, "confirmed": 0, "error": str(e)}
    for biz, rev in attr.get("by_cell", {}).items():
        if biz in cells and not cells[biz].get("excluded"):
            cells[biz]["confirmed_revenue_aud"] = rev
            # پول‌بر‌درصد: اگر flag روشن است، CONFIRMED AUD را به value score تزریق کن.
            # رابطهٔ واقعی: شاخکی که دلارِ CONFIRMED می‌سازد → value بالاتر → fitness بالاتر.
            if os.environ.get("OCTOPUS_WIRE_BARBELL") == "1":
                rev_signal = min(1.0, float(rev or 0) / 1000.0)   # کران [0,1]: AU$1000 → سقف
                boosted_value = 0.5 * (cells[biz].get("acceptance_rate") or 0.0) + 0.5 * rev_signal
                cells[biz]["fitness"] = round(
                    weights.get("value", .3) * boosted_value
                    + weights.get("urgency", .25) * 0.0
                    + weights.get("efficiency", .2) * cells[biz].get("efficiency", 0.0)
                    + weights.get("human", .2) * 0.5
                    - weights.get("waste", .05) * cells[biz].get("waste", 0.0), 4)
                cells[biz]["revenue_boost_applied"] = True

    report = {
        "ts": opslib.now_iso(),
        "authoritative": span >= AUTHORITATIVE_AFTER_DAYS,
        "experience_span_days": span,
        "authoritative_note": ("قفل verdict جلسه ۱۶: تا ~۴ هفته دادهٔ ledger فقط سایه"
                               if span < AUTHORITATIVE_AFTER_DAYS else "بازهٔ داده کافی است"),
        "acceptance_source": "logs/outbox.jsonl ⟂ core.db/outbox (فقط بعد از کلیک انسان)",
        "integrity_alerts": tamper,
        "attribution": {"revenue_by_cell": attr.get("by_cell", {}),
                        "coverage": attr.get("attribution_coverage"),
                        "claimed": attr.get("claimed", 0), "confirmed": attr.get("confirmed", 0),
                        "note": "فقط CONFIRMED؛ فرمولِ fitness هنوز شادو — این سیگنالِ پولِ محقق است"},
        "cells": cells,
        "weights": weights,
    }
    if write:
        with opslib.LockedJson(opslib.STATE_DIR / "fitness-latest.json") as lj:
            lj.write(report)
        with opslib.LockedJson(HISTORY) as lj:
            lj.write(history)
    return report


if __name__ == "__main__":
    print(json.dumps(compute(write="--dry" not in sys.argv), ensure_ascii=False, indent=2))
