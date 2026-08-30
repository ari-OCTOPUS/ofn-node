"""
brain/events.py — گذرگاهِ رویدادِ ساختاریافته برای داشبورد اتوماسیون.

به‌جای لاگِ متنِ آزاد، هر ماژول یک event ساختاریافته منتشر می‌کند که در SQLite
ذخیره می‌شود؛ داشبورد از همین رویدادها وضعیت خلاصه و actionable می‌سازد.

رویدادهای استاندارد:
    task.started · task.completed · task.failed · task.blocked
    handoff.created · system.heartbeat · approval.required

هر رویداد فیلدهای ثابتی دارد (approval_state همیشه مقدار صریح دارد، نه null مبهم).
"""
from __future__ import annotations

import sqlite3
import uuid
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Optional

logger = logging.getLogger(__name__)

# نامِ رویدادهای معتبر
VALID_EVENTS = {
    "task.started",
    "task.completed",
    "task.failed",
    "task.blocked",
    "handoff.created",
    "system.heartbeat",
    "approval.required",
    "kernel.notice",
    # C-012 فاز صفر (Council Mesh v0.1) — telemetry حلقهٔ حافظه:
    "memory.read",       # خواندنِ حافظه پیش از تصمیم (منبعِ ratio ≥ 0.95)
    "memory.readback",   # read-back پس از نوشتن (منبعِ ratio ≥ 0.99)
}

# وضعیت‌های approval — همیشه صریح (نه null)
APPROVAL_STATES = {"unknown", "not_required", "pending", "approved", "rejected"}


@dataclass
class Event:
    """یک رویدادِ ساختاریافته."""
    timestamp: str
    trace_id: str
    agent_id: str
    event_name: str
    status: str            # ok | error | blocked | pending | info | retry
    summary: str
    duration_ms: int = 0
    next_action: str = ""
    approval_state: str = "unknown"


def _db_path():
    from memory.store import DB_PATH
    return str(DB_PATH)


# C3 fix: پرچمِ idempotent — _ensure_events_table فقط یک‌بار در هر فرایند اجرا می‌شود.
# قبلاً هر emit دو کانکشن باز می‌کرد (یکی برای ensure، یکی برای INSERT).
_table_ready = False


def _ensure_events_table(conn=None):
    """ایجادِ جدولِ dashboard_events اگر نباشد. idempotent (یک‌بار در هر فرایند).

    C3 fix: اگر یک کانکشن داده شود، روی همان اجرا می‌شود (بدونِ کانکشنِ اضافه).
    اگر پرچمِ module-level ست شده باشد و کانکشن داده نشده باشد، skip می‌شود.
    """
    global _table_ready
    if conn is not None:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS dashboard_events (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp      TEXT NOT NULL,
                trace_id       TEXT,
                agent_id       TEXT,
                event_name     TEXT NOT NULL,
                status         TEXT,
                summary        TEXT,
                duration_ms    INTEGER DEFAULT 0,
                next_action    TEXT DEFAULT '',
                approval_state TEXT DEFAULT 'unknown'
            );
            CREATE INDEX IF NOT EXISTS idx_dash_events_id ON dashboard_events(id DESC);
        """)
        conn.commit()
        _table_ready = True
        return

    if _table_ready:
        return
    from memory.store import DB_PATH
    DB_PATH.parent.mkdir(exist_ok=True)
    c = sqlite3.connect(str(DB_PATH), timeout=30)
    try:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS dashboard_events (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp      TEXT NOT NULL,
                trace_id       TEXT,
                agent_id       TEXT,
                event_name     TEXT NOT NULL,
                status         TEXT,
                summary        TEXT,
                duration_ms    INTEGER DEFAULT 0,
                next_action    TEXT DEFAULT '',
                approval_state TEXT DEFAULT 'unknown'
            );
            CREATE INDEX IF NOT EXISTS idx_dash_events_id ON dashboard_events(id DESC);
        """)
        c.commit()
    finally:
        c.close()
    _table_ready = True


def new_trace_id() -> str:
    """یک شناسه‌ی trace کوتاه و یکتا."""
    return uuid.uuid4().hex[:8]


def emit(event_name: str, summary: str, *,
         status: str = "info", agent_id: str = "system",
         trace_id: Optional[str] = None, duration_ms: int = 0,
         next_action: str = "", approval_state: str = "unknown") -> Event:
    """انتشار یک رویداد و ذخیره در SQLite. شیء Event برمی‌گرداند."""
    if event_name not in VALID_EVENTS:
        logger.warning("emit(): unknown event_name %r (stored anyway)", event_name)
    if approval_state not in APPROVAL_STATES:
        approval_state = "unknown"

    ev = Event(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        trace_id=trace_id or new_trace_id(),
        agent_id=agent_id,
        event_name=event_name,
        status=status,
        summary=summary,
        duration_ms=int(duration_ms),
        next_action=next_action,
        approval_state=approval_state,
    )

    _ensure_events_table()
    # C3 fix: یک کانکشن (نه دو) + timeout=30 مثل store.py.
    conn = sqlite3.connect(_db_path(), timeout=30)
    try:
        # اطمینان از وجودِ جدول روی همین کانکشن (cheap اگر جدول از قبل هست)
        conn.execute("SELECT 1 FROM dashboard_events LIMIT 1")
    except sqlite3.OperationalError:
        _ensure_events_table(conn=conn)
    try:
        conn.execute(
            """INSERT INTO dashboard_events
               (timestamp, trace_id, agent_id, event_name, status, summary,
                duration_ms, next_action, approval_state)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ev.timestamp, ev.trace_id, ev.agent_id, ev.event_name, ev.status,
             ev.summary, ev.duration_ms, ev.next_action, ev.approval_state),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info("event %-18s [%-7s] %s", ev.event_name, ev.status, ev.summary)
    return ev


def get_recent(limit: int = 30) -> list[dict]:
    """آخرین رویدادها (جدیدترین اول)."""
    _ensure_events_table()
    conn = sqlite3.connect(_db_path(), timeout=30)
    try:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM dashboard_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def latest_of(event_names) -> Optional[dict]:
    """آخرین رویداد از میان نام‌های داده‌شده (برای کارت‌های Now/Last/Attention)."""
    if isinstance(event_names, str):
        event_names = [event_names]
    names = list(event_names)
    if not names:
        return None
    _ensure_events_table()
    placeholders = ",".join("?" * len(names))
    conn = sqlite3.connect(_db_path(), timeout=30)
    try:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            f"SELECT * FROM dashboard_events WHERE event_name IN ({placeholders}) "
            f"ORDER BY id DESC LIMIT 1", names
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def get_summary(window_seconds: int = 300) -> dict:
    """خلاصه‌ی آماری رویدادهای پنجره‌ی اخیر (پیش‌فرض ۵ دقیقه).

    C4 fix: به‌جای مقایسهٔ رشته‌ایِ ISO (fragile با tz/DST)، ردیف‌ها را
    می‌خواند و با datetime.parse مقایسه می‌کند. این مقاوم‌تر است.
    """
    _ensure_events_table()
    cutoff_dt = datetime.now() - timedelta(seconds=window_seconds)
    conn = sqlite3.connect(_db_path(), timeout=30)
    try:
        rows = conn.execute(
            "SELECT event_name, status, timestamp FROM dashboard_events"
        ).fetchall()
    finally:
        conn.close()

    # فیلتر با datetime.parse (مقاوم در برابرِ tz/DST)
    total = completed = errors = retries = pending = heartbeats = 0
    for name, status, ts_str in rows:
        try:
            ts = datetime.fromisoformat(str(ts_str))
        except (ValueError, TypeError):
            continue  # ردیفِ خراب → نادیده
        if ts < cutoff_dt:
            continue
        total += 1
        if name == "task.completed":
            completed += 1
        elif name == "task.failed":
            errors += 1
        elif status == "retry":
            retries += 1
        elif name == "approval.required":
            pending += 1
        elif name == "system.heartbeat":
            heartbeats += 1

    return {
        "window_seconds": window_seconds,
        "total": total,
        "completed": completed,
        "errors": errors,
        "retries": retries,
        "pending": pending,
        "heartbeats": heartbeats,
    }


def counts() -> dict:
    """شمارشِ کل (همه‌ی تاریخچه) برای KPIها."""
    _ensure_events_table()
    conn = sqlite3.connect(_db_path(), timeout=30)
    try:
        done = conn.execute(
            "SELECT COUNT(*) FROM dashboard_events WHERE event_name='task.completed'"
        ).fetchone()[0]
        errors = conn.execute(
            "SELECT COUNT(*) FROM dashboard_events WHERE event_name='task.failed'"
        ).fetchone()[0]
        pending = conn.execute(
            "SELECT COUNT(*) FROM dashboard_events WHERE approval_state='pending'"
        ).fetchone()[0]
        blocked = conn.execute(
            "SELECT COUNT(*) FROM dashboard_events WHERE event_name='task.blocked'"
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM dashboard_events").fetchone()[0]
    finally:
        conn.close()
    return {"done": done, "errors": errors, "pending": pending,
            "blocked": blocked, "total": total}


def resolve_latest_approval(new_state: str) -> bool:
    """وضعیتِ آخرین approvalِ در انتظار را به approved/rejected تغییر می‌دهد."""
    if new_state not in ("approved", "rejected"):
        return False
    _ensure_events_table()
    conn = sqlite3.connect(_db_path(), timeout=30)
    try:
        row = conn.execute(
            "SELECT id FROM dashboard_events WHERE approval_state='pending' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return False
        conn.execute(
            "UPDATE dashboard_events SET approval_state=? WHERE id=?",
            (new_state, row[0])
        )
        conn.commit()
    finally:
        conn.close()
    return True


def clear_events() -> int:
    """پاک‌کردن همه‌ی رویدادها (برای ریست لاگ). تعداد حذف‌شده را برمی‌گرداند."""
    _ensure_events_table()
    conn = sqlite3.connect(_db_path(), timeout=30)
    try:
        n = conn.execute("SELECT COUNT(*) FROM dashboard_events").fetchone()[0]
        conn.execute("DELETE FROM dashboard_events")
        conn.commit()
    finally:
        conn.close()
    return n


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    clear_events()
    tid = new_trace_id()
    emit("task.started", "شروع کاوش #1", status="info", agent_id="autoloop", trace_id=tid)
    emit("task.completed", "کشف ذخیره شد: physical:Lorenz · MI=0.87",
         status="ok", agent_id="autoloop", trace_id=tid, duration_ms=420, next_action="ادامه")
    emit("approval.required", "کشف مهم — نیاز به تایید", status="blocked",
         agent_id="autoloop", approval_state="pending", next_action="تایید شما")
    print("recent:", len(get_recent()))
    print("counts:", counts())
    print("summary:", get_summary())
