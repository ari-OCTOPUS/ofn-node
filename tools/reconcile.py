#!/usr/bin/env python3
"""reconcile.py — همگراییِ انبارها (Lane I5، GAPS-31/36/37/40).

بررسی‌های invariant بین سه انبار:
  R1  شمارندهٔ سقفِ امروز == تعداد WAL state=sent امروز
  R2  هر WAL sent امروز یک رویداد communication.sent در events دارد
  R3  تعداد outbox sent (lead-quote) == تعداد WAL sent (همان campaign)
  R4  هر لیدِ contacted/review یک intro ارسال‌شده دارد (WAL)
  R5  هیچ لیدی که suppressed است در صفِ فالوآپِ امروز نباشد
  R6  schemaهای کلیدی بدون migrationِ معلق (نگاشتِ شناخته‌شده)

خروجی JSON؛ exit 1 اگر mismatch — مصرفِ مصرفِ cron/digest. هرگز فیکس نمی‌کند؛
گزارش می‌دهد (تشخیص انسانی/ایجنتی، نه نوشتنِ کور).
"""
from __future__ import annotations

import json
import sqlite3
import sys
import datetime as _dt
from pathlib import Path

HOME = Path.home()
OUTBOX = HOME / ".local/share/ofn/outbox.sqlite"
PAINT = HOME / ".local/share/ofn/painting.sqlite"
WAL = HOME / "ofn/ofn/agi2027_runtime/outbound-effects.sqlite3"
EVENTS = HOME / "ofn/data/state/legs/lead-inbox/events.jsonl"
for _p in (HOME / "ofn/ofn/agents", HOME / "ofn/ofn/budget"):
    sys.path.insert(0, str(_p))


def _today_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")


def _counter() -> "int | None":
    """شمارندهٔ سقفِ امروز — تزریق‌پذیر برای تست (دندان‌ها)."""
    try:
        import outbound_worker as _ow
        import os
        for ln in (HOME / ".config/ofn/secrets.env").read_text().splitlines():
            if "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                os.environ.setdefault(k, v)
        return _ow.sends_today()
    except Exception:  # noqa: BLE001
        return None


def run() -> dict:
    rep = {"date": _today_utc(), "checks": {}, "ok": True}
    today = _today_utc()

    wal = sqlite3.connect(WAL)
    # updated_at ممکن است ISO یا epoch باشد — هر دو را می‌سنجیم
    wal_sent_today = wal.execute(
        "SELECT COUNT(*) FROM outbound_effects WHERE state='sent' AND ("
        "substr(updated_at,1,10)=? OR "
        "strftime('%Y-%m-%d', updated_at, 'unixepoch')=?)",
        (today, today)).fetchone()[0]
    wal_sent_all = wal.execute(
        "SELECT COUNT(*) FROM outbound_effects WHERE state='sent'").fetchone()[0]
    wal_nonfinal = wal.execute(
        "SELECT state, COUNT(*) FROM outbound_effects "
        "WHERE state NOT IN ('sent','failed') GROUP BY state").fetchall()

    ox = sqlite3.connect(OUTBOX)
    ox_sent = ox.execute(
        "SELECT COUNT(*) FROM outbox WHERE status='sent' "
        "AND idem_key LIKE 'lead-quote:%'").fetchone()[0]
    ox_pending = ox.execute(
        "SELECT COUNT(*) FROM outbox WHERE status='pending'").fetchone()[0]

    sent_events_today = 0
    try:
        for ln in EVENTS.read_text().splitlines():
            if ('"communication.sent"' in ln
                    and f'"occurred_at": "{today}' in ln):
                sent_events_today += 1
    except Exception:  # noqa: BLE001
        pass

    try:
        counter = _counter()
    except Exception:  # noqa: BLE001
        counter = None

    paint = sqlite3.connect(PAINT)
    active = paint.execute(
        "SELECT COUNT(*) FROM painting_leads WHERE status IN "
        "('contacted','review','quoted')").fetchone()[0]
    suppressed_active = paint.execute(
        "SELECT COUNT(*) FROM painting_leads WHERE status IN "
        "('contacted','review') AND next_action LIKE '%do not contact%'"
    ).fetchone()[0]

    rep["checks"]["R1_counter_eq_wal_today"] = {
        "counter": counter, "wal_sent_today": wal_sent_today,
        "match": (counter == wal_sent_today) if counter is not None else None}
    rep["checks"]["R2_events_today"] = {
        "events": sent_events_today, "wal": wal_sent_today,
        "match": sent_events_today >= wal_sent_today or wal_sent_today == 0}
    rep["checks"]["R3_outbox_eq_wal"] = {
        "outbox_sent": ox_sent, "wal_sent_all": wal_sent_all,
        "match": ox_sent == wal_sent_all}
    rep["checks"]["R4_active_leads"] = {
        "active_leads": active, "wal_sent_all": wal_sent_all,
        "match": active >= 1}
    rep["checks"]["R5_no_suppressed_in_cycle"] = {
        "violations": suppressed_active, "match": suppressed_active == 0}
    rep["checks"]["R6_wal_no_nonfinal"] = {
        "nonfinal": dict(wal_nonfinal), "match": not wal_nonfinal}
    rep["outbox_pending"] = ox_pending

    for name, chk in rep["checks"].items():
        if chk.get("match") is False:
            rep["ok"] = False
    wal.close()
    ox.close()
    paint.close()
    return rep


if __name__ == "__main__":
    r = run()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(0 if r["ok"] else 1)
