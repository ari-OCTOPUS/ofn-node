"""R16 — سیاست چرخهٔ عمر صف فرضیه (مصوب مالک 2026-08-16، «همرو موافقم»).

سند: 02-DECISIONS/DECISION-ARTIFACTS-2026-08-16/R16-HYPOTHESIS-QUEUE-POLICY-v1.md
پنج قاعده: dormancy نرم ۹۰روزه · dedup خانواده‌ای · سقف ورود ۱۰/روز ·
ارجاع الزامی برای برداشتن از صف · مهاجرت یک‌بارهٔ تراکنشی.

قید سخت: حذف ممنوع (append-only) — همهٔ گذارها برچسب‌اند، ردیف می‌ماند؛
هر گذار در hypothesis_policy_events ثبت می‌شود (قابل rollback).
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone

POLICY_VERSION = "R16-v1"
DAILY_CAP = 10                # قاعدهٔ ۳ — سقف ورودِ فعالِ نو در روز
DORMANCY_DAYS = 90            # قاعدهٔ ۱ — انقضای نرم
FAMILY_PREFIX = 80            # قاعدهٔ ۲ — کلید خانواده (پیشوندِ نرمال‌شده)
# بذر دستورکار (research_agenda) ورودِ مولد نیست — سقف را پر نمی‌کند.
CAP_EXEMPT_DOMAIN_PREFIX = "brain-os"

_STATUS_ACTIVE = "pending"


def family_key(domain: str, hypothesis: str) -> str:
    """کلید خانواده — همان فرمولِ گزارشِ قدم صفر (hypothesis_queue_report)."""
    norm = re.sub(r"\s+", " ", str(hypothesis or "").lower())[:FAMILY_PREFIX]
    return f"{str(domain or '؟')}::{norm}"


def _ensure_policy_columns(conn: sqlite3.Connection) -> None:
    """افزودنیِ امن — ستون‌های سیاست (idempotent)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(hypotheses)").fetchall()}
    if "policy_tag" not in cols:
        conn.execute("ALTER TABLE hypotheses ADD COLUMN policy_tag TEXT")
    if "dedup_of" not in cols:
        conn.execute("ALTER TABLE hypotheses ADD COLUMN dedup_of INTEGER")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS hypothesis_policy_events (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               applied_at TEXT NOT NULL,
               policy_version TEXT NOT NULL,
               action TEXT NOT NULL,
               row_id INTEGER NOT NULL,
               old_status TEXT,
               detail TEXT
           )"""
    )
    conn.commit()


def _log(conn, action: str, row_id: int, old_status: str | None, detail: str) -> None:
    conn.execute(
        "INSERT INTO hypothesis_policy_events (applied_at, policy_version, action,"
        " row_id, old_status, detail) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"),
         POLICY_VERSION, action, row_id, old_status, detail),
    )


def classify_for_insert(conn: sqlite3.Connection, domain: str,
                        hypothesis: str, today: str | None = None) -> tuple[str, int | None]:
    """تصمیمِ ورود برای یک فرضیهٔ نو: (status, dedup_of).

    'dedup' ⇒ خانوادهٔ موجود، head برمی‌گردد · 'deferred' ⇒ سقف روز پر ·
    'pending' ⇒ فعال. ارجاعِ الزامی (قاعدهٔ ۴) در صفِ مصرف اعمال می‌شود نه ورود.
    """
    _ensure_policy_columns(conn)
    today = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # خانواده: قدیمی‌ترین عضوِ فعالِ هم‌کلید
    key = family_key(domain, hypothesis)
    prefix = key.split("::", 1)[1]
    row = conn.execute(
        "SELECT id FROM hypotheses WHERE domain = ? AND status = ?"
        " AND substr(lower(replace(replace(hypothesis, char(10), ' '), char(9), ' ')), 1, ?)"
        "   = substr(?, 1, ?) ORDER BY id LIMIT 1",
        (domain, _STATUS_ACTIVE, FAMILY_PREFIX, prefix, FAMILY_PREFIX),
    ).fetchone()
    if row:
        return "dedup", int(row[0])
    active_today = conn.execute(
        "SELECT COUNT(*) FROM hypotheses WHERE substr(timestamp, 1, 10) = ?"
        " AND status = ? AND IFNULL(domain, '') NOT LIKE ?",
        (today, _STATUS_ACTIVE, CAP_EXEMPT_DOMAIN_PREFIX + "%"),
    ).fetchone()[0]
    if active_today >= DAILY_CAP:
        return "deferred", None
    return "pending", None


def migration_dry_run(conn: sqlite3.Connection) -> dict:
    """diff قابل‌بازبینی قاعده‌های ۱و۲ روی وضعیت فعلی — بدون هیچ تغییری."""
    _ensure_policy_columns(conn)
    rows = conn.execute(
        "SELECT id, timestamp, domain, hypothesis, status FROM hypotheses"
        " ORDER BY id").fetchall()
    now = datetime.now(timezone.utc)
    families: dict[str, int] = {}
    plan: list[dict] = []
    for hid, ts, domain, hyp, status in rows:
        if status != _STATUS_ACTIVE:
            continue
        key = family_key(domain, hyp)
        head = families.get(key)
        age_days: int | None = None
        try:
            t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            age_days = (now - t).days
        except ValueError:
            pass
        if head is None:
            families[key] = hid
            # قاعدهٔ ۱ روی head هم اعمال می‌شود
            if age_days is not None and age_days > DORMANCY_DAYS:
                plan.append({"id": hid, "to": "dormant", "reason": f"age={age_days}d"})
        else:
            plan.append({"id": hid, "to": "dedup", "head": head, "reason": "family"})
    from collections import Counter
    by_action = Counter(p["to"] for p in plan)
    return {
        "policy_version": POLICY_VERSION,
        "total_rows": len(rows),
        "active_before": sum(1 for r in rows if r[4] == _STATUS_ACTIVE),
        "active_after": sum(1 for r in rows if r[4] == _STATUS_ACTIVE) - len(plan),
        "changes": len(plan),
        "by_action": dict(by_action),
        "sample": plan[:12],
        "deletions": 0,
    }


def apply_migration(conn: sqlite3.Connection) -> dict:
    """اعمالِ تراکنشیِ همان برنامهٔ dry-run — قابل rollback از روی لاگ."""
    plan_summary = migration_dry_run(conn)
    heads: dict[str, int] = {}
    rows = conn.execute(
        "SELECT id, domain, hypothesis FROM hypotheses WHERE status = ?"
        " ORDER BY id", (_STATUS_ACTIVE,)).fetchall()
    for hid, domain, hyp in rows:
        key = family_key(domain, hyp)
        head = heads.get(key)
        if head is None:
            heads[key] = hid
            continue
        conn.execute(
            "UPDATE hypotheses SET status='dedup', dedup_of=?, policy_tag=? WHERE id=?",
            (head, f"{POLICY_VERSION}:family:{head}", hid))
        _log(conn, "family-dedup", hid, _STATUS_ACTIVE, f"head={head}")
    # dormancy روی آنچه ماند
    now = datetime.now(timezone.utc)
    remaining = conn.execute(
        "SELECT id, timestamp FROM hypotheses WHERE status = ?", (_STATUS_ACTIVE,)).fetchall()
    for hid, ts in remaining:
        try:
            t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if (now - t).days > DORMANCY_DAYS:
                conn.execute(
                    "UPDATE hypotheses SET status='dormant', policy_tag=? WHERE id=?",
                    (f"{POLICY_VERSION}:dormancy:{(now - t).days}d", hid))
                _log(conn, "dormancy", hid, _STATUS_ACTIVE, f"age={(now - t).days}d")
        except ValueError:
            continue
    conn.commit()
    after = conn.execute(
        "SELECT COUNT(*) FROM hypotheses WHERE status = ?", (_STATUS_ACTIVE,)).fetchone()[0]
    plan_summary["active_after_actual"] = after
    return plan_summary


def rollback_last_migration(conn: sqlite3.Connection) -> int:
    """واگردِ آخرین دستهٔ مهاجرت (بر اساس لاگ) — فقط گذارهای همین policy_version."""
    _ensure_policy_columns(conn)
    rows = conn.execute(
        "SELECT row_id, old_status FROM hypothesis_policy_events"
        " WHERE policy_version = ? ORDER BY id DESC", (POLICY_VERSION,)).fetchall()
    n = 0
    for row_id, old_status in rows:
        conn.execute(
            "UPDATE hypotheses SET status=?, policy_tag=NULL, dedup_of=NULL WHERE id=?",
            (old_status or _STATUS_ACTIVE, row_id))
        n += 1
    conn.execute("DELETE FROM hypothesis_policy_events WHERE policy_version = ?",
                 (POLICY_VERSION,))
    conn.commit()
    return n
