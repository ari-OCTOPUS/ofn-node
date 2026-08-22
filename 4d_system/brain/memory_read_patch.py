"""
brain/memory_read_patch.py — حلقهٔ خواندنِ حافظه (C-012 فاز صفر، Council Mesh v0.1).

پیش از این، automation.py فقط می‌نوشت (save_hypothesis/save_experiment) و هرگز
حافظه را نمی‌خواند — حلقهٔ یادگیری write-only بود (دفتر تناقض‌ها: C-012).
این ماژول خواندن را به سه نقطهٔ تصمیم وصل می‌کند:

  introspect — بازیابیِ تجربهٔ گذشته + آمارِ حافظه، پیش از خودخوانی
  create     — dedup فرضیه + شمارشِ صفِ راکد (stale)، پیش از ثبتِ فرضیهٔ نو
  conclude   — بازیابیِ بافتِ والت (RAG)، پیش از نتیجه‌گیری

هر خواندن یک رویدادِ `memory.read` و هر read-backِ پس از نوشتن یک رویدادِ
`memory.readback` در dashboard_events ثبت می‌کند — همین رویدادها منبعِ
دو متریکِ پذیرشِ فاز صفر هستند:

  memory_read_before_decision_ratio   هدف ≥ 0.95
  memory_readback_success_ratio       هدف ≥ 0.99

زمان‌بندی (نگاشتِ صادقانه به شمای موجود — additive، بدون تغییرِ شِما):
  transaction_time = ستونِ timestamp (لحظهٔ ثبتِ ردیف در DB)
  valid_time       = بازهٔ اعتبارِ فرضیهٔ pending (تا وقتی tested=0)
  stale            = pending با transaction_time کهنه‌تر از stale_days
"""
from __future__ import annotations

import difflib
import logging
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# عامل‌هایی که «تصمیم» می‌گیرند و باید پیش از تصمیم حافظه بخوانند.
# (نام‌های agent_id در رویدادهای task.* همان‌هاست که automation.py منتشر می‌کند.)
DECISION_AGENTS = ("creative", "conclude", "introspect")

# آستانهٔ شباهتِ dedup — بالای این حد، ایدهٔ نو «تکرارِ» فرضیهٔ pending تلقی می‌شود.
DUPLICATE_SIMILARITY_THRESHOLD = 0.90

# فرضیهٔ pending که از این روزها قدیمی‌تر باشد راکد (stale) است.
STALE_DAYS_DEFAULT = 14

_ZWNJ = "\u200c"  # نیم‌فاصلهٔ فارسی — در نرمال‌سازی یکسان‌سازی می‌شود
_WORD_RE = re.compile(r"[\w\u0600-\u06FF]+")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    """naive → UTC فرضی (سازگار با timestampهای قدیمی)؛ aware → UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


# ── خواننده‌ها (هر کدام telemetry می‌فرستند) ─────────────────────────────

def read_past_experiments(limit: int = 5, trace_id: str | None = None) -> list[dict]:
    """خواندنِ تجربه‌های گذشته — با رویدادِ memory.read در traceِ کارِ تصمیم."""
    t0 = time.perf_counter()
    rows: list = []
    ok = False
    try:
        from memory.store import query_experiments
        rows = query_experiments(limit=limit) or []
        ok = True
    except Exception as e:
        logger.warning("query_experiments failed: %s", e)
    _emit_read("experiments", len(rows), t0, purpose=f"limit={limit}",
               trace_id=trace_id, ok=ok)
    return rows


def read_pending_hypotheses(limit: int = 10, trace_id: str | None = None) -> list[dict]:
    """خواندنِ فرضیه‌های در انتظار — با رویدادِ memory.read در traceِ کارِ تصمیم."""
    t0 = time.perf_counter()
    rows: list = []
    ok = False
    try:
        from memory.store import get_pending_hypotheses
        rows = get_pending_hypotheses(limit=limit) or []
        ok = True
    except Exception as e:
        logger.warning("get_pending_hypotheses failed: %s", e)
    _emit_read("hypotheses", len(rows), t0, purpose=f"limit={limit}",
               trace_id=trace_id, ok=ok)
    return rows


def search_vault_memory(query: str, n: int = 3, trace_id: str | None = None):
    """جستجوی RAG در والت — با رویدادِ memory.read در traceِ کارِ تصمیم.

    از `memory.vectorstore.search_vault` می‌خواند، نه `brain.tools.search_vault`.
    دومی با @toolِ langchain دکوره شده، پس یک StructuredTool است نه تابع و
    صدا زدنش TypeError می‌دهد (تأییدشده روی langchain_core 1.4.9)؛ ضمناً رشتهٔ
    قالب‌بندی‌شده برمی‌گرداند که len() رویش کاراکتر می‌شمارد نه نُت — و چون در
    خطا هم رشتهٔ ناتهیِ "Search error: ..." می‌دهد، خرابیِ کامل عددِ بزرگ‌تری
    از یک بازیابیِ واقعی می‌ساخت. این یکی list[dict] می‌دهد، پس شمارش واقعی است.
    """
    t0 = time.perf_counter()
    result = None
    ok = False
    try:
        from memory.vectorstore import search_vault
        result = search_vault(query, k=n) or []
        ok = True
    except Exception as e:
        logger.warning("search_vault failed: %s", e)
    rows = len(result) if result else 0
    _emit_read("vault_rag", rows, t0, purpose=f"q={query[:40]!r}",
               trace_id=trace_id, ok=ok)
    return result


def get_memory_stats() -> dict:
    """آمارِ کلیّتِ حافظه (بدون telemetry — زیر مجموعهٔ خوانده‌های دیگر است)."""
    try:
        from memory.store import get_stats
        return get_stats()
    except Exception:
        return {}


# ── قلاب‌های سه‌نقطه‌ای (برای استفادهٔ مستقیم در automation) ───────────────

def patch_introspect(ctrl, trace_id: str | None = None, limit: int = 5) -> dict:
    """introspect: تجربهٔ گذشته + آمار، پیش از خودخوانی.

    همان ردیف‌هایی که شمرده می‌شوند جلو می‌روند؛ پیش از این `past` عددِ ۵ را
    گزارش می‌کرد ولی فقط `[:3]` به تصمیم می‌رسید.
    """
    past = read_past_experiments(limit, trace_id=trace_id)
    return {"past": len(past), "stats": get_memory_stats(), "experiments": past}


def patch_create(ctrl, trace_id: str | None = None, limit: int = 200,
                 stale_days: int = STALE_DAYS_DEFAULT) -> dict:
    """create: صفِ فرضیه‌های pending، پیش از خلاقیت (برای dedup).

    ردیف‌های کامل برمی‌گردند نه یک متنِ بریده: is_duplicate_hypothesis به خودِ
    ردیف‌ها نیاز دارد، و شمردنِ ۲۰۰ ردیف در حالی که فقط چند تای اولش داخلِ
    ۵۰۰ کاراکتر جا می‌شد، عدد را چند برابرِ اثرِ واقعی نشان می‌داد.
    """
    p = read_pending_hypotheses(limit, trace_id=trace_id)
    stale, fresh = split_stale(p, stale_days)
    return {"existing": len(p), "pending": p,
            "stale": len(stale), "fresh": len(fresh)}


def patch_conclude(ctrl, topic: str = "", trace_id: str | None = None,
                   n: int = 3) -> dict:
    """conclude: بافتِ والت، پیش از نتیجه‌گیری.

    وقتی topic خالی است بازیابی به تصمیم مشروط نیست؛ با conditioned=False
    علامت می‌خورد تا شمارشِ حاصل از یک پرس‌وجوی ثابت با بازیابیِ واقعاً
    مرتبط اشتباه گرفته نشود.
    """
    conditioned = bool(topic and topic.strip())
    query = topic.strip() if conditioned else "hidden dimension SOG"
    r = search_vault_memory(query, n, trace_id=trace_id)
    return {"vault": len(r) if r else 0, "context": r,
            "conditioned": conditioned, "query": query}


# ── dedup و stale ────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """نرمال‌سازیِ مقایسه — حذفِ نیم‌فاصله/نشانه‌ها، یکسان‌سازیِ فاصله وケース."""
    if not text:
        return ""
    t = str(text).replace(_ZWNJ, " ").casefold()
    return " ".join(_WORD_RE.findall(t))


def hypothesis_similarity(a: str, b: str) -> float:
    """شباهتِ ۰..۱ بین دو متنِ فرضیه (بر پایهٔ توکن‌های نرمال‌شده)."""
    na, nb = normalize_text(a), normalize_text(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = set(na.split()), set(nb.split())
    jaccard = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    seq = difflib.SequenceMatcher(None, na, nb).ratio()
    return max(jaccard, seq)


def is_duplicate_hypothesis(idea: str, pending: list[dict],
                            threshold: float = DUPLICATE_SIMILARITY_THRESHOLD) -> bool:
    """آیا ایدهٔ نو تکرارِ یکی از فرضیه‌های pending است؟"""
    for row in pending or []:
        if hypothesis_similarity(idea, str(row.get("hypothesis", ""))) >= threshold:
            return True
    return False


def split_stale(pending: list[dict], stale_days: int = STALE_DAYS_DEFAULT,
                now: datetime | None = None):
    """تفکیکِ pending به (stale, fresh) بر پایهٔ transaction_time (ستونِ timestamp).

    ستونِ timestamp لحظهٔ ثبت در DB است (transaction_time)؛ فرضیهٔ pendingِ
    بدونِ tested برایش valid_time نامتناهی است — کهنگیِ ثبت، نشانهٔ صفِ راکد.
    """
    now = _as_utc(now) if now is not None else _now()
    cutoff = now - timedelta(days=stale_days)
    stale, fresh = [], []
    for row in pending or []:
        try:
            ts = datetime.fromisoformat(str(row.get("timestamp", "")).replace("Z", "+00:00"))
            ts = _as_utc(ts)
        except (ValueError, TypeError):
            fresh.append(row)  # ردیفِ بی‌زمان → محافظه‌کارانهً تازه
            continue
        (stale if ts < cutoff else fresh).append(row)
    return stale, fresh


# ── read-back پس از نوشتن (از مسیرِ مصرف‌کننده) ──────────────────────────

def readback_hypothesis(hid: int, scan_limit: int = 50, trace_id: str | None = None) -> bool:
    """تأییدِ نوشته پس از نوشتن — همان مسیری که مصرف‌کننده می‌خواند.

    فرضیهٔ تازه جدیدترین timestamp را دارد، پس در HEADِ
    get_pending_hypotheses (ORDER BY timestamp DESC) باید دیده شود.
    """
    t0 = time.perf_counter()
    ok = False
    note = ""
    try:
        from memory.store import get_pending_hypotheses
        rows = get_pending_hypotheses(limit=scan_limit) or []
        ok = any(r.get("id") == hid for r in rows)
        if not ok:
            # R16 (2026-08-16): سطرِ نو ممکن است درج لحظه‌ای dedup/deferred خورده
            # باشد و عمداً بیرونِ صفِ فعال باشد. نمای مصرف‌کنندهٔ درستِ آن
            # وضعیت = خواندنِ مستقیمِ همان id از همان DB که مصرف‌کننده می‌خواند
            # (connection تازه، همان مسیر store) — نوشتهٔ خواندنی = تأیید.
            import sqlite3 as _sq
            from config.settings import OUTPUT_DIR
            con = _sq.connect(f"file:{OUTPUT_DIR / '4d_experiments.db'}?mode=ro",
                              uri=True)
            row = con.execute(
                "SELECT status FROM hypotheses WHERE id = ?", (hid,)).fetchone()
            con.close()
            if row and row[0] in ("dedup", "deferred", "dormant"):
                ok = True
                note = f"(r16-view:{row[0]})"
    except Exception as e:
        logger.debug("readback failed: %s", e)
    _emit_readback(ok, hid, t0, trace_id=trace_id, note=note)
    return ok


# ── telemetry ────────────────────────────────────────────────────────────

def _emit_read(source: str, rows: int, t0: float, purpose: str = "",
               trace_id: str | None = None, ok: bool = True) -> None:
    """ثبتِ رویدادِ memory.read — بدونِ شکستنِ کارِ اصلی (best-effort).

    trace_id همان traceِ کارِ تصمیم است تا متریکِ read-before-decision
    بتواند خواندن را به کارِ مصرف‌کننده پیوند بزند.

    status از `ok`ِ خودِ خواننده می‌آید، نه از `rows`. شرطِ قبلی
    (`rows is not None`) روی یک int همیشه درست بود، پس هر خواندن — حتی
    خواندنی که استثنا خورده و صفر ردیف برگردانده — «ok» ثبت می‌شد؛ یعنی
    دقیقاً همان سبزِ دروغینی که این تله‌متری برای ردش ساخته شده.
    """
    try:
        from brain import events
        events.emit(
            "memory.read",
            f"خواندنِ {source} → {rows} ردیف · {purpose}",
            status="ok" if ok else "error",
            agent_id=f"memory:{source}",
            trace_id=trace_id,
            duration_ms=int((time.perf_counter() - t0) * 1000),
            next_action="مصرف در تصمیم" if ok else "بررسیِ خطای خواندن",
        )
    except Exception as e:
        logger.debug("memory.read telemetry failed: %s", e)


def _emit_readback(ok: bool, hid: int, t0: float, trace_id: str | None = None,
                   note: str = "") -> None:
    try:
        from brain import events
        events.emit(
            "memory.readback",
            f"read-back فرضیه #{hid} — {'تأیید شد' if ok else 'یافت نشد!'}{note}",
            status="ok" if ok else "error",
            agent_id="memory:readback",
            trace_id=trace_id,
            duration_ms=int((time.perf_counter() - t0) * 1000),
            next_action="ادامه" if ok else "بررسی",
        )
    except Exception as e:
        logger.debug("memory.readback telemetry failed: %s", e)


def max_event_id() -> int:
    """بزرگ‌ترین id رویداد — برای علامت‌گذاریِ مرزِ یک اجرای زنده.

    DB تازه بدونِ هیچ رویدادی → 0 (نه خطا — پنجرهٔ «از ابتدا»).
    """
    from brain import events as ev
    conn = sqlite3.connect(ev._db_path(), timeout=30)
    try:
        try:
            row = conn.execute("SELECT MAX(id) FROM dashboard_events").fetchone()
        except sqlite3.OperationalError:
            return 0
        return int(row[0] or 0)
    finally:
        conn.close()


def telemetry_metrics(after_id: int = 0) -> dict:
    """دو متریکِ پذیرشِ فاز صفر، محاسبه‌شده از تاریخچهٔ نگه‌داری‌شدهٔ رویدادها.

    memory_read_before_decision_ratio:
      از میانِ کارهای تصمیم (task.completed|task.failed با agent_id در
      DECISION_AGENTS و trace_id)، سهمِ آن‌ها که پیش از رویدادِ پایانشان
      یک memory.read با همان trace_id دارند.
    memory_readback_success_ratio:
      سهمِ رویدادهای memory.readback با status=ok.

    housekeeping ردیف‌های قدیمیِ dashboard_events را به events_archive منتقل
    می‌کند. سنجه باید هر دو جدول را بخواند؛ وگرنه after_id=0 به‌مرور فقط پنجرهٔ
    تازه را «کل تاریخ» جا می‌زند و شکست‌های قدیمی ناپدید می‌شوند.
    """
    from brain import events as ev
    conn = sqlite3.connect(ev._db_path(), timeout=30)
    try:
        conn.row_factory = sqlite3.Row
        try:
            existing = {
                row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
            tables = [
                name for name in ("events_archive", "dashboard_events")
                if name in existing
            ]
            selects = [
                f"SELECT id, event_name, agent_id, trace_id, status FROM {name} "
                "WHERE id > ?"
                for name in tables
            ]
            rows = conn.execute(
                " UNION ALL ".join(selects) + " ORDER BY id ASC",
                tuple(after_id for _ in tables),
            ).fetchall() if selects else []
        except sqlite3.OperationalError:
            rows = []  # جدول‌ها هنوز ساخته نشده‌اند — پنجرهٔ تهی
    finally:
        conn.close()

    reads_by_trace: dict[str, list[int]] = {}
    decisions: list[dict] = []
    readback_total = readback_ok = 0
    for r in rows:
        name, agent, trace = r["event_name"], r["agent_id"], r["trace_id"]
        if name == "memory.read":
            if trace:
                reads_by_trace.setdefault(trace, []).append(r["id"])
        elif name == "memory.readback":
            readback_total += 1
            if r["status"] == "ok":
                readback_ok += 1
        elif name in ("task.completed", "task.failed") and agent in DECISION_AGENTS and trace:
            decisions.append({"id": r["id"], "trace": trace})

    with_read = sum(
        1 for d in decisions
        if any(rid < d["id"] for rid in reads_by_trace.get(d["trace"], []))
    )
    return {
        "after_id": after_id,
        "decision_jobs": len(decisions),
        "decision_jobs_with_read": with_read,
        "memory_read_before_decision_ratio": (with_read / len(decisions)) if decisions else None,
        "readback_total": readback_total,
        "readback_ok": readback_ok,
        "memory_readback_success_ratio": (readback_ok / readback_total) if readback_total else None,
        "phase_zero_targets": {"read_before_decision": 0.95, "readback": 0.99},
    }
