"""run_store.py — Cognitive Runtime: Run Store adapter (minimum viable).

روی JSONL فایل موجود می‌نشیند (state/cognitive/runs/<run_id>.jsonl).
دقیقاً مطابق convention مخزن: append-only، JSONL، fail-soft.
بدون سرویس خارجی. durability = PROCESS_DURABLE (فایل روی دیسک، ولی no fsync guarantee).

API:
    create_run(run_id, trace_id, metadata) -> run dict
    append_event(run_id, event_type, ...) -> sequence number
    get_run(run_id) -> run dict | None
    list_events(run_id, after_sequence=0) -> list[event]
    mark_terminal(run_id, status) -> bool
"""
from __future__ import annotations

import contextlib
import json
import os
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

try:                                   # POSIX
    import fcntl as _fcntl
except ImportError:                    # pragma: no cover — Windows
    _fcntl = None
try:                                   # Windows
    import msvcrt as _msvcrt
except ImportError:                    # pragma: no cover — POSIX
    _msvcrt = None

_OPS = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("OCTOPUS_STATE_DIR", str(_OPS / "state")))
RUNS_DIR = STATE_DIR / "cognitive" / "runs"

# 2026-08-23 — از PROCESS_DURABLE به SERIALIZED_APPEND ارتقا یافت.
# قبلاً append_event یک read-modify-write ِ بی‌قفل بود و دو نویسندهٔ هم‌زمان
# روی یک run_id هم sequence تکراری می‌ساختند و هم — چون نوشتن‌ها وسطِ خط
# درهم می‌رفتند و `_read_jsonl` خطای JSON را بی‌صدا `continue` می‌کرد — رویداد
# را کاملاً گم می‌کردند. شاهدِ بازتولیدشده: ۹۶ append → ۶۷ شمارهٔ یکتا + ۲ رویدادِ
# نابودشده (`_ops/tests/test_run_store_concurrency.py`، قبل از فیکس).
# حالا کلِ بخشِ بحرانی (خواندن → محاسبهٔ seq → نوشتن) زیرِ قفلِ فایلیِ
# بین‌پروسه‌ای است — نه قفلِ درون‌پروسه‌ای، چون درسِ ثبت‌شدهٔ این مخزن این است
# که RLock پروسهٔ دوم را نمی‌بیند.
LOCK_TIMEOUT_S = 30.0
DURABILITY = "SERIALIZED_APPEND"  # قفلِ فایلی بین‌پروسه‌ای؛ همچنان no fsync guarantee
SCHEMA = "cognitive-run-store.v1"


def _run_path(run_id: str) -> Path:
    safe = "".join(c for c in run_id if c.isalnum() or c in "-_")[:64]
    return RUNS_DIR / f"{safe}.jsonl"


def _lock_path(run_id: str) -> Path:
    """قفل در زیرپوشهٔ جدا می‌نشیند تا RUNS_DIR فقط فایل‌های داده داشته باشد."""
    safe = "".join(c for c in run_id if c.isalnum() or c in "-_")[:64]
    return RUNS_DIR / ".locks" / f"{safe}.lock"


def _acquire(fh) -> None:
    if _fcntl is not None:
        _fcntl.flock(fh.fileno(), _fcntl.LOCK_EX)
        return
    if _msvcrt is not None:
        deadline = time.monotonic() + LOCK_TIMEOUT_S
        while True:
            try:
                fh.seek(0)
                _msvcrt.locking(fh.fileno(), _msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.005)
    # هیچ primitive ِ قفلی نیست: تنزل به رفتارِ قبلی، نه crash (fail-soft).


def _release(fh) -> None:
    try:
        if _fcntl is not None:
            _fcntl.flock(fh.fileno(), _fcntl.LOCK_UN)
        elif _msvcrt is not None:
            fh.seek(0)
            _msvcrt.locking(fh.fileno(), _msvcrt.LK_UNLCK, 1)
    except OSError:
        pass


@contextlib.contextmanager
def _exclusive(run_id: str):
    """قفلِ انحصاریِ بین‌پروسه‌ای روی یک run_id.

    هر فراخوانی handle خودش را باز می‌کند؛ روی هر دو پلتفرم قفل به
    open-file-description گره می‌خورد، پس بینِ **نخ‌های یک پروسه** هم کار می‌کند.
    """
    lp = _lock_path(run_id)
    lp.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lp, "a+b")
    try:
        _acquire(fh)
        yield
    finally:
        _release(fh)
        fh.close()


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if isinstance(d, dict):
                out.append(d)
        except json.JSONDecodeError:
            # ⚠ بلعِ عمدیِ خطِ خراب. تا قبل از فیکسِ قفل (۲۰۲۶-۰۸-۲۳) همین خط
            # بود که گم‌شدنِ رویداد را **بی‌صدا** می‌کرد: نوشتنِ هم‌زمان خط را
            # نصفه می‌کرد و اینجا بی‌هیچ ردی دور انداخته می‌شد. حالا که نوشتن
            # سریال است این حالت نباید رخ دهد؛ اگر رخ داد یعنی یا قفل کار نکرده
            # یا فایل از بیرون دستکاری شده — هر دو خبرِ بد. عمداً همچنان
            # fail-soft می‌ماند (خواندن نباید چت را بکشد) ولی اگر روزی نیازِ
            # هشدار شد، نقطه‌اش همین‌جاست. رجوع: TDR-DBOS-RUNSTORE.md §3.
            continue
    return out


def create_run(run_id: str, *, trace_id: str | None = None,
               metadata: dict | None = None) -> dict:
    """یک run جدید بساز. RUN_CREATED در فایل ذخیره می‌شود."""
    rec = {
        "schema": SCHEMA,
        "event_id": f"evt_{uuid4().hex[:16]}",
        "event_type": "RUN_CREATED",
        "run_id": run_id,
        "trace_id": trace_id or f"trace_{uuid4().hex[:12]}",
        "sequence": 0,
        "occurred_at": _utc(),
        "producer": "run_store",
        "status": "CREATED",
        "state": "CREATED",
        "durability": DURABILITY,
        "metadata": metadata or {},
        "redaction_applied": True,
        "may_authorize": False,
        "applied": False,
    }
    with _exclusive(run_id):
        _append_jsonl(_run_path(run_id), rec)
    return rec


def append_event(run_id: str, event_type: str, *,
                 trace_id: str | None = None,
                 producer: str = "system",
                 status: str = "COMPLETED",
                 intent: str | None = None,
                 payload: dict | None = None,
                 evidence_refs: list | None = None) -> int:
    """یک event به run اضافه کن و sequence برگردان.

    کلِ خواندن→محاسبهٔ seq→نوشتن زیرِ یک قفلِ انحصاری است. نوشتن هم باید داخلِ
    قفل باشد نه فقط محاسبه: نوشتنِ هم‌زمان خطوط را درهم می‌کرد و
    `_read_jsonl` خطِ خرابِ حاصل را بی‌صدا دور می‌انداخت ⇒ گم‌شدنِ کاملِ رویداد.
    """
    # redaction: فیلتر کلیدهای حساس از payload (بیرونِ قفل — کارِ خالصِ CPU)
    safe_payload = {}
    if payload:
        for k, v in payload.items():
            if k.lower() not in ("text", "prompt", "dm", "content", "raw",
                                  "api_key", "token", "secret"):
                safe_payload[k] = v

    with _exclusive(run_id):
        events = _read_jsonl(_run_path(run_id))
        max_seq = max((e.get("sequence", 0) for e in events), default=-1)
        seq = max_seq + 1
        rec = {
            "event_id": f"evt_{uuid4().hex[:16]}",
            "event_type": event_type,
            "event_version": 1,
            "run_id": run_id,
            "trace_id": trace_id,
            "sequence": seq,
            "occurred_at": _utc(),
            "producer": producer,
            "status": status,
            "intent": intent,
            "payload": safe_payload,
            "evidence_refs": evidence_refs or [],
            "redaction_applied": True,
            "may_authorize": False,
            "applied": False,
        }
        _append_jsonl(_run_path(run_id), rec)
        # state update برای terminal events — قفل از قبل در دست است، پس نسخهٔ
        # خصوصیِ بی‌قفل صدا می‌شود (قفل reentrant نیست).
        if event_type == "RUN_COMPLETED":
            _mark_terminal(run_id, "COMPLETED")
        elif event_type == "RUN_FAILED":
            _mark_terminal(run_id, "FAILED")
        elif event_type == "RUN_CANCELLED":
            _mark_terminal(run_id, "CANCELLED")
    return seq


def get_run(run_id: str) -> dict | None:
    """آخرین state یک run."""
    events = _read_jsonl(_run_path(run_id))
    if not events:
        return None
    last = events[-1]
    return {
        "run_id": run_id,
        "trace_id": last.get("trace_id"),
        "state": last.get("state") or _state_from_events(events),
        "sequence": last.get("sequence", 0),
        "event_count": len(events),
        "durability": DURABILITY,
        "created_at": events[0].get("occurred_at") if events else None,
        "may_authorize": False,
    }


def list_events(run_id: str, after_sequence: int = -1) -> list[dict]:
    """eventهای یک run از sequence مشخص (default: همه)."""
    events = _read_jsonl(_run_path(run_id))
    return [e for e in events if e.get("sequence", 0) > after_sequence]


def _state_from_events(events: list[dict]) -> str:
    for e in reversed(events):
        et = e.get("event_type", "")
        if et == "RUN_COMPLETED": return "COMPLETED"
        if et == "RUN_FAILED": return "FAILED"
        if et == "RUN_CANCELLED": return "CANCELLED"
    return "ACTIVE"


def _mark_terminal(run_id: str, state: str) -> None:
    """state را در فایل علامت بزن (از طریق آخرین event).

    ⚠ بی‌قفل عمدی — **صداکننده باید قفلِ run را در دست داشته باشد**
    (`append_event` دارد). نقطهٔ ورودِ عمومیِ قفل‌دار: `mark_terminal()`.
    """
    # terminal event خودش در append ثبت شده؛ این فقط marker است
    marker = {
        "event_id": f"evt_{uuid4().hex[:16]}",
        "event_type": f"RUN_MARKED_{state}",
        "run_id": run_id,
        "sequence": -1,  # marker نه event واقعی
        "occurred_at": _utc(),
        "producer": "run_store",
        "state": state,
        "may_authorize": False,
    }
    _append_jsonl(_run_path(run_id), marker)


def mark_terminal(run_id: str, status: str) -> bool:
    """external API برای علامت‌گذاری terminal (قفل را خودش می‌گیرد)."""
    if status not in ("COMPLETED", "FAILED", "CANCELLED"):
        return False
    with _exclusive(run_id):
        _mark_terminal(run_id, status)
    return True
