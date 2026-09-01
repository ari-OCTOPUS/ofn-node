"""daily_digest — گزارشِ صبحگاهیِ مالک (Lane I4، رأی Q7).

از events.jsonl ۲۴ ساعتِ گذشته + وضعیتِ لیدها/کوت‌ها، یک پیامِ فارسیِ خوانا
می‌سازد و با owner_notify می‌فرستد. چیزی که امروز لازم است مالک بداند:
ارسال‌ها، جواب‌ها، کوت‌ها، پول، سلامت.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "budget"))
import opslib  # noqa: E402
import owner_notify  # noqa: E402

PAINTING_DB = Path.home() / ".local/share/ofn/painting.sqlite"
EVENTS = opslib.STATE_DIR / "legs" / "lead-inbox" / "events.jsonl"


def _recent_events(hours=24) -> list[dict]:
    import datetime as _dt
    out = []
    try:
        cutoff = (_dt.datetime.now(_dt.timezone.utc) -
                  _dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M")
        for ln in EVENTS.read_text().splitlines():
            try:
                d = json.loads(ln)
                if str(d.get("occurred_at", ""))[:16] >= cutoff:
                    out.append(d)
            except Exception:  # noqa: BLE001
                continue
    except Exception:  # noqa: BLE001
        pass
    return out


def compose(hours: int = 24) -> str:
    evs = _recent_events(hours)
    kinds = {}
    for e in evs:
        kinds[e.get("event_type", "?")] = kinds.get(e.get("event_type", "?"), 0) + 1
    c = sqlite3.connect(PAINTING_DB)
    c.row_factory = sqlite3.Row
    leads = {r["status"]: r["n"] for r in c.execute(
        "SELECT status, COUNT(*) n FROM painting_leads GROUP BY status")}
    c.execute("CREATE TABLE IF NOT EXISTS painting_quotes ("
              "qt_number TEXT PRIMARY KEY, lead_id TEXT, scope_json TEXT, "
              "priced INTEGER, total_aud REAL, status TEXT, created_at TEXT)")
    quotes = c.execute("SELECT COUNT(*) FROM painting_quotes").fetchone()
    won = c.execute("SELECT COUNT(*) FROM painting_leads WHERE status='won'"
                    ).fetchone()[0]
    booked = c.execute("SELECT COALESCE(SUM(booked_amount_cents),0) FROM "
                       "painting_leads").fetchone()[0] / 100.0
    won_pending = c.execute(
        "SELECT COUNT(*) FROM painting_leads WHERE status='won' "
        "AND (booked_amount_cents IS NULL OR booked_amount_cents=0)"
    ).fetchone()[0]
    c.close()
    lines = [
        "📊 گزارشِ روزانهٔ اختاپوس",
        f"رویدادهای ۲۴ ساعت: {len(evs)}",
    ]
    for k in sorted(kinds):
        lines.append(f"  · {k}: {kinds[k]}")
    lines.append(f"لیدها: " + " · ".join(f"{k}={v}" for k, v in leads.items()))
    try:
        lines.append(f"کوت‌ها: {quotes[0]} · برنده: {won} · در انتظار تأیید پول: {won_pending}")
    except Exception:  # noqa: BLE001
        pass
    lines.append(f"💰 کتاب‌شده (تأییدشده): ${booked:,.0f}")
    if won_pending:
        lines.append("⏳ یک قرارداد won بدون مبلغ ثبت‌شده است — با /quotes تأیید کن تا booked شود.")
    return "\n".join(lines)


def run(hours: int = 24, dry: bool = False) -> dict:
    text = compose(hours)
    if dry:
        return {"text": text, "dry": True}
    return {"text": text, "tg": owner_notify.send(text)}


if __name__ == "__main__":
    print(json.dumps(run(dry="--dry" in sys.argv), ensure_ascii=False, indent=1))
