"""airtasker_intake.py — AIRTASKER-WIRE 2026-09-08 (owner GO «وصلش کن»).

طبقهٔ چهارمِ گوشِ OCTOPUS در کنار reply/bounce/optout: ایمیلِ هشدارِ Airtasker.
وصلتِ وبسایت به ارگانیسم: alert email → پارس → لید (فقط افزودنی) → کارت تلگرام.
پیشنهاد دادن روی تسک همیشه دستی می‌ماند (رجیستری: manual_monitor /
"manual proposal only") — این ماژول هیچ‌وقت به Airtasker چیزی نمی‌فرستد.

قرارداد (آینهٔ imap_listener):
  - هرگز raise نمی‌کند؛ خروجی dict برای لاگ cycle.
  - dry=True فقط می‌شمارد و می‌پارسد؛ هیچ نوشتنی (DB/رسید/تلگرام) ندارد.
  - جعل ممنوع: فیلد غایب = '' می‌ماند (قرارداد پارسر: None → '').
  - supply_risk=True هرگز لید نمی‌شود (فلسفهٔ kill-metric wrong_recipient).
  - dedupe با source_ref (URL تسک) — ایمیل تکراری = بی‌اثر idempotent.
  - receipt در events.jsonl از طریق opslib (همان زنجیرهٔ موجود).

مسیر DB: همان painting.sqlite که imap_listener می‌خواند
(قابل override با env AIRTASKER_INTAKE_DB برای تست).
"""
from __future__ import annotations

import email.message
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (str(_HERE), str(_HERE.parent / "budget")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402  (same env as imap_listener on 138)

EVENTS_PATH = opslib.STATE_DIR / "legs" / "airtasker-watch" / "events.jsonl"
MAX_CARDS_PER_EMAIL = 3   # ضد-اسپم تلگرام؛ بقیه فقط در رسید ثبت می‌شوند

SUPPORTED_SENDER_ENV = "AIRTASKER_EXTRA_SENDER_SUFFIXES"

# بردِ سریع #1 (BLACKBOX-BRIDGE، رأی «ادامه»): امتیازِ شفافِ قاعده‌محور —
# بدون مدل، بدون جعل؛ فقط از فیلدهای پارس‌شده. ستون score در painting_leads.
def _score(task) -> tuple:
    s, why = 0, []
    if task.budget_text:
        s += 40
        why.append("budget")
    if task.location_text:
        s += 30
        why.append("loc")
    if task.task_id:
        s += 10
        why.append("id")
    if not task.supply_risk:
        s += 20
        why.append("demand")
    return s, ("score:" + "+".join(why) if why else "score:0")


def _bump_daily(counter_path: Path, key: str) -> None:
    """بردِ سریع #2: شمارندهٔ روزانه (خواندنی برای doctor/digestهای بعدی)."""
    import datetime
    try:
        data = {}
        if counter_path.exists():
            data = json.loads(counter_path.read_text(encoding="utf-8"))
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        day = data.setdefault(today, {"emails": 0, "tasks": 0, "inserted": 0})
        day[key] = day.get(key, 0) + 1
        counter_path.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass


def _db_path() -> Path:
    return Path(os.environ.get("AIRTASKER_INTAKE_DB")
                or Path.home() / ".local/share/ofn/painting.sqlite")


def _receipt(event_type: str, payload: dict) -> None:
    try:
        opslib.append_jsonl(EVENTS_PATH, {
            "event_id": opslib.now_iso() + "-" + event_type,
            "event_type": event_type, "occurred_at": opslib.now_iso(),
            "source_component": "AirtaskerIntake", "schema_version": "1.0",
            "payload": payload})
    except Exception:  # noqa: BLE001 — رسید هرگز مسیر را نمی‌کشد
        pass


def _notify_owner(text: str) -> None:
    try:
        import owner_notify
        owner_notify.alert_owner(text)
    except Exception:  # noqa: BLE001 — تلگرام اختیاری است
        pass


def handle_airtasker_alert(msg: email.message.Message, dry: bool = False,
                           sender: str = "") -> dict:
    """پارس ایمیل هشدار + درج لیدهای تازه + کارت تلگرام. هرگز raise نمی‌کند."""
    import airtasker_alert_parser as parser
    out: dict = {"alert": "airtasker", "dry": bool(dry)}
    try:
        alert = parser.parse_alert_message(msg)
    except Exception as exc:  # noqa: BLE001 — پارسر خودش fail-closed است، ولی مطمئن
        out["error"] = f"parse:{type(exc).__name__}"
        if not dry:
            _receipt("airtasker.parse_error", {"detail": type(exc).__name__})
        return out

    fresh, skipped_risk, dupes, inserted = [], 0, 0, 0
    cards: list[str] = []
    for task in alert.tasks:
        if task.supply_risk:
            skipped_risk += 1
            continue
        fresh.append(task)

    out.update({"tasks_seen": len(alert.tasks), "supply_risk_skipped": skipped_risk,
                "parse_errors": alert.errors[:5]})

    if dry:
        out["would_insert"] = [t.url for t in fresh][:10]
        return out

    import sqlite3
    now = opslib.now_iso()
    con = sqlite3.connect(_db_path())
    try:
        for task in fresh:
            try:
                row = con.execute(
                    "SELECT lead_id FROM painting_leads "
                    "WHERE source='airtasker' AND source_ref=?",
                    (task.url,)).fetchone()
                if row:
                    dupes += 1
                    continue
                lead_id = f"at:{task.task_id}" if task.task_id else (
                    "at:" + __import__("hashlib").sha1(
                        task.url.encode()).hexdigest()[:12])
                sc, sc_why = _score(task)
                con.execute(
                    "INSERT INTO painting_leads (lead_id, source, source_ref, "
                    "suburb, budget_text, message, temperature, status, "
                    "created_at, updated_at, notes, score) VALUES "
                    "(?, 'airtasker', ?, ?, ?, ?, 'new', 'new', ?, ?, ?, ?)",
                    (lead_id, task.url, task.location_text or "",
                     task.budget_text or "", task.title or task.url,
                     now, now,
                     "AIRTASKER-WIRE auto-intake; proposal stays manual; " + sc_why,
                     sc))
                inserted += 1
                _receipt("airtasker.alert_seen", {
                    "lead_id": lead_id, "url": task.url,
                    "title": task.title or "", "budget_text": task.budget_text or "",
                    "location": task.location_text or ""})
                if len(cards) < MAX_CARDS_PER_EMAIL:
                    cards.append(f"🎨 {task.to_card()}")
            except Exception as exc:  # noqa: BLE001 — یک تسک خراب بقیه را نکشد
                _receipt("airtasker.insert_error",
                         {"url": task.url[:120], "detail": type(exc).__name__})
        con.commit()
    finally:
        con.close()

    out.update({"inserted": inserted, "dupes": dupes,
                "cards_sent": len(cards)})
    _bump_daily(EVENTS_PATH.parent / "daily-counter.json", "emails")
    for _k, _v in (("tasks", len(alert.tasks)), ("inserted", inserted)):
        for _ in range(_v):
            _bump_daily(EVENTS_PATH.parent / "daily-counter.json", _k)
    if alert.subject:
        _receipt("airtasker.email_processed", {
            "subject": alert.subject[:120], "from": (sender or "")[:60],
            "tasks": len(alert.tasks), "fresh": len(fresh),
            "skipped_risk": skipped_risk})
    for c in cards:
        _notify_owner(c)
    return out
