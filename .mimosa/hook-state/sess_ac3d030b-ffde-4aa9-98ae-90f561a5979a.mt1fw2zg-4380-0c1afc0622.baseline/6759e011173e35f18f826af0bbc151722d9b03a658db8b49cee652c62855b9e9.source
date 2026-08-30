#!/usr/bin/env python3
"""tracer.py — Agent telemetry tracer برای CH-11.

نقش: trace هر function call (duration، args hash، result status) و ارسال به
unified_bus + log محلی. content-free: هیچ secret/محتوای خصوصی لاگ نمی‌شود؛
فقط hash از args + type از result.

ویژگی‌ها:
  • @trace(agent_id=...) decorator — هر call را auto-trace می‌کند.
  • trace_span(...) context manager — block دستی trace.
  • trace_id / span_id — همبستگی بینِ spans.
  • unified_bus.publish("TRACE", ...) — ارسال به ledger.
  • fallback jsonl — اگر bus نباشد، local trace log.

قرارداد:
  • status ∈ {"ok", "error", "timeout", "blocked"}
  • args_hash = sha256(str(args_types))[:16] — content-free fingerprint
  • result_hint = type(result).__name__ — هیچ value لاگ نمی‌شود
  • همهٔ exceptions در tracer داخلی fail-soft — خرابی trace نباید function را بکشد.

وابستگی: stdlib-only؛ opslib برای paths؛ unified_bus اختیاری (injectable).
"""
from __future__ import annotations

import functools
import hashlib
import json
import logging
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Optional

# ─── paths (از opslib یا fallback) ───────────────────────────────────────────
_HERE = Path(__file__).resolve().parent  # _ops/observability/
_OPS = _HERE.parent
_STATE = _OPS / "state"

# تلاش برای import opslib؛ اگر نشد، fallback local
opslib: Any = None  # type: ignore[assignment]
try:
    sys.path.insert(0, str(_OPS / "budget"))
    import opslib as _opslib  # noqa: E402
    opslib = _opslib
except Exception:
    pass


def _state_dir() -> Path:
    if opslib is not None:
        return getattr(opslib, "STATE_DIR", _STATE)
    return _STATE


# ─── logging ─────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
if not logger.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s — %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)

# ─── thread-local trace stack ────────────────────────────────────────────────
_TLS = threading.local()


def _current_trace_id() -> str:
    return getattr(_TLS, "trace_id", "")


def _push_span(span_id: str) -> None:
    if not hasattr(_TLS, "span_stack"):
        _TLS.span_stack = []
    _TLS.span_stack.append(span_id)


def _pop_span() -> None:
    stack = getattr(_TLS, "span_stack", None)
    if stack:
        stack.pop()


def _current_span_id() -> str:
    stack = getattr(_TLS, "span_stack", None)
    return stack[-1] if stack else ""


# ─── content-free helpers ────────────────────────────────────────────────────
def _args_hash(args: tuple, kwargs: dict) -> str:
    """fingerprint content-free از args: فقط type_names، نه values."""
    try:
        sig = {
            "args_types": [type(a).__name__ for a in args],
            "kwargs_types": {k: type(v).__name__ for k, v in kwargs.items()},
        }
        raw = json.dumps(sig, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]
    except Exception:
        return "hash-err"


def _result_hint(result: Any) -> str:
    """فقط type_name از result — هیچ value."""
    try:
        return type(result).__name__
    except Exception:
        return "unknown"


def _exc_type_hint(exc: BaseException) -> str:
    return type(exc).__name__


# ─── trace record builder ────────────────────────────────────────────────────
def _build_record(
    *,
    agent_id: str,
    operation: str,
    trace_id: str,
    span_id: str,
    parent_span_id: str,
    duration_ms: float,
    status: str,
    args_hash: str,
    result_hint: str,
    exc_hint: str = "",
    meta: Optional[dict] = None,
) -> dict:
    """یک رکورد trace ساختاریافته می‌سازد (content-free)."""
    return {
        "ts": time.time(),
        "timestamp": _iso_now(),
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "agent_id": str(agent_id)[:40],
        "operation": str(operation)[:80],
        "duration_ms": round(duration_ms, 3),
        "status": status,
        "args_hash": args_hash,
        "result_hint": result_hint,
        "exc_hint": exc_hint,
        "meta": dict(meta) if meta else {},
    }


def _iso_now() -> str:
    import datetime as _dt
    return _dt.datetime.now().isoformat(timespec="seconds")


# ─── unified_bus publisher (fail-soft، injectable) ───────────────────────────
_BUS: Any = None
_BUS_LOCK = threading.Lock()


def _get_bus() -> Any:
    """lazy load unified_bus؛ اگر نبود → None (fallback به local log)."""
    global _BUS
    if _BUS is not None:
        return _BUS
    with _BUS_LOCK:
        if _BUS is not None:
            return _BUS
        try:
            sys.path.insert(0, str(_OPS))
            import unified_bus as _ub  # noqa: E402
            _BUS = _ub.UnifiedBus()
        except Exception:
            logger.debug("unified_bus not available — trace will use local log only")
            _BUS = None
    return _BUS


def _inject_bus(bus: Any) -> None:
    """برای تست: bus مصنوعی تزریق کن."""
    global _BUS
    _BUS = bus


# ─── local trace log (fallback) ──────────────────────────────────────────────
TRACE_LOG: Path = _state_dir() / "traces.jsonl"
_MAX_LOCAL = 2000


def _append_local(record: dict) -> None:
    """append به traces.jsonl؛ اگر بزرگ شد → rotate."""
    try:
        TRACE_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(TRACE_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        # rotate اگر از حد گذشت
        try:
            if TRACE_LOG.stat().st_size > _MAX_LOCAL * 200:
                _rotate_log()
        except OSError:
            pass
    except OSError as e:
        logger.warning("trace local log failed: %s", e)


def _rotate_log() -> None:
    """backup قدیمی و شروع نو."""
    try:
        bak = TRACE_LOG.with_suffix(".jsonl.bak")
        if bak.exists():
            bak.unlink()
        TRACE_LOG.rename(bak)
    except OSError:
        pass


def _publish(record: dict) -> None:
    """ابتدا bus؛ اگر نشد local. همیشه fail-soft."""
    bus = _get_bus()
    if bus is not None:
        try:
            bus.publish(
                event_type="TRACE",
                payload=record,
                actor=record.get("agent_id", "tracer"),
                is_human=False,
            )
        except Exception as e:
            logger.debug("bus publish failed: %s", e)
    # همیشه local هم بنویس (redundant but safe)
    _append_local(record)


# ─── public API: trace_span context manager ──────────────────────────────────
@contextmanager
def trace_span(
    operation: str,
    agent_id: str = "system",
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    meta: Optional[dict] = None,
):
    """Context manager برای trace کردن یک block.

    Usage:
        with trace_span("compute_batch", agent_id="analyst") as span:
            result = heavy_work()
            span["result_hint"] = "list"
    """
    _tid = trace_id or _current_trace_id() or uuid.uuid4().hex[:12]
    _sid = uuid.uuid4().hex[:8]
    _pid = parent_span_id or _current_span_id()

    # set thread-local
    old_trace = getattr(_TLS, "trace_id", None)
    _TLS.trace_id = _tid
    _push_span(_sid)

    span_meta: dict = dict(meta) if meta else {}
    t0 = time.perf_counter()
    status = "ok"
    exc_hint = ""
    try:
        yield span_meta
    except Exception as exc:
        status = "error"
        exc_hint = _exc_type_hint(exc)
        raise
    finally:
        dur = (time.perf_counter() - t0) * 1000
        rec = _build_record(
            agent_id=agent_id,
            operation=operation,
            trace_id=_tid,
            span_id=_sid,
            parent_span_id=_pid,
            duration_ms=dur,
            status=status,
            args_hash="",
            result_hint=span_meta.get("result_hint", ""),
            exc_hint=exc_hint,
            meta=span_meta,
        )
        _publish(rec)
        # restore thread-local
        _pop_span()
        if old_trace is not None:
            _TLS.trace_id = old_trace
        elif hasattr(_TLS, "trace_id"):
            delattr(_TLS, "trace_id")


# ─── public API: trace decorator ─────────────────────────────────────────────
def trace(
    agent_id: Optional[str] = None,
    operation: Optional[str] = None,
    trace_id: Optional[str] = None,
    pass_span: bool = False,
):
    """Decorator برای auto-trace یک function.

    Usage:
        @trace(agent_id="analyst")
        def analyze(data):
            return result

    اگر pass_span=True → last arg را span dict می‌گذارد (برای result_hint).
    """
    def decorator(fn: Callable) -> Callable:
        _op = operation or fn.__name__
        _aid = agent_id or getattr(fn, "__module__", "unknown").split(".")[-1]

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            _tid = trace_id or _current_trace_id() or uuid.uuid4().hex[:12]
            _sid = uuid.uuid4().hex[:8]
            _pid = _current_span_id()

            old_trace = getattr(_TLS, "trace_id", None)
            _TLS.trace_id = _tid
            _push_span(_sid)

            ahash = _args_hash(args, kwargs)
            t0 = time.perf_counter()
            status = "ok"
            result_hint = ""
            exc_hint = ""
            result = None

            # اگر pass_span=True → kwargs["_span_meta"] inject
            if pass_span:
                kwargs = dict(kwargs, _span_meta={})
                span_ref = kwargs["_span_meta"]
            else:
                span_ref = None

            try:
                result = fn(*args, **kwargs)
                result_hint = _result_hint(result)
                if span_ref is not None:
                    span_ref["result_hint"] = result_hint
                return result
            except Exception as exc:
                status = "error"
                exc_hint = _exc_type_hint(exc)
                raise
            finally:
                dur = (time.perf_counter() - t0) * 1000
                rec = _build_record(
                    agent_id=_aid,
                    operation=_op,
                    trace_id=_tid,
                    span_id=_sid,
                    parent_span_id=_pid,
                    duration_ms=dur,
                    status=status,
                    args_hash=ahash,
                    result_hint=result_hint,
                    exc_hint=exc_hint,
                )
                _publish(rec)
                _pop_span()
                if old_trace is not None:
                    _TLS.trace_id = old_trace
                elif hasattr(_TLS, "trace_id"):
                    delattr(_TLS, "trace_id")

        # برای دسترسی به raw function (تست)
        wrapper.__wrapped__ = fn  # type: ignore[attr-defined]
        return wrapper
    return decorator


# ─── trace log reader / utilities ────────────────────────────────────────────
def read_traces(limit: int = 200) -> list[dict]:
    """خواندن آخرین traces از local log."""
    try:
        if not TRACE_LOG.exists():
            return []
        lines = TRACE_LOG.read_text("utf-8").splitlines()
        out = []
        for ln in lines[-limit:]:
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
        return out
    except OSError:
        return []


def trace_summary(window_seconds: float = 300) -> dict:
    """خلاصهٔ traces در پنجرهٔ اخیر."""
    cutoff = time.time() - window_seconds
    traces = [t for t in read_traces(limit=1000) if t.get("ts", 0) >= cutoff]
    total = len(traces)
    errors = sum(1 for t in traces if t.get("status") == "error")
    blocked = sum(1 for t in traces if t.get("status") == "blocked")
    timeouts = sum(1 for t in traces if t.get("status") == "timeout")
    ok = total - errors - blocked - timeouts
    by_agent: dict = {}
    by_op: dict = {}
    for t in traces:
        by_agent[t.get("agent_id", "?")] = by_agent.get(t.get("agent_id", "?"), 0) + 1
        by_op[t.get("operation", "?")] = by_op.get(t.get("operation", "?"), 0) + 1
    dur_list = [t.get("duration_ms", 0) for t in traces if t.get("duration_ms")]
    avg_dur = round(sum(dur_list) / len(dur_list), 2) if dur_list else 0
    max_dur = round(max(dur_list), 2) if dur_list else 0
    return {
        "window_seconds": int(window_seconds),
        "total": total,
        "ok": ok,
        "errors": errors,
        "blocked": blocked,
        "timeouts": timeouts,
        "avg_duration_ms": avg_dur,
        "max_duration_ms": max_dur,
        "by_agent": by_agent,
        "by_operation": by_op,
    }


def span_tree(trace_id: str) -> list[dict]:
    """همهٔ spans یک trace را به ترتیبِ زمانی برمی‌گرداند."""
    return sorted(
        [t for t in read_traces(limit=1000) if t.get("trace_id") == trace_id],
        key=lambda x: x.get("ts", 0),
    )


# ─── smoke test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    @trace(agent_id="tester")
    def add(a, b):
        return a + b

    @trace(agent_id="tester")
    def fail():
        raise ValueError("boom")

    print("add(2,3) =", add(2, 3))
    try:
        fail()
    except ValueError:
        pass

    with trace_span("manual_block", agent_id="tester") as sm:
        sm["stage"] = "compute"
        time.sleep(0.01)
        sm["result_hint"] = "dict"

    print("trace_summary:", json.dumps(trace_summary(), ensure_ascii=False, indent=2))
    print("traces count:", len(read_traces()))
