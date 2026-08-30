"""
tracer.py — دکوریتورِ trace برای شفافیتِ pipeline.

سبک است: نام و موفقیت/خطای فراخوانی را در یک sinkِ اختیاری ثبت می‌کند.
sink یک callable(name, status, info) است (مثلاً به event_log وصل می‌شود).
"""

from __future__ import annotations

import functools
import logging

log = logging.getLogger("langar.trace")
_SINK = None


def set_sink(fn) -> None:
    global _SINK
    _SINK = fn


def _emit(name, status, info=""):
    log.debug("trace %s %s %s", name, status, info)
    if _SINK:
        try:
            _SINK(name, status, info)
        except Exception:
            pass


def trace(name: str | None = None):
    def deco(func):
        tname = name or func.__name__

        @functools.wraps(func)
        def wrapper(*a, **k):
            try:
                r = func(*a, **k)
                _emit(tname, "ok")
                return r
            except Exception as e:
                _emit(tname, "error", repr(e))
                raise
        return wrapper
    return deco
