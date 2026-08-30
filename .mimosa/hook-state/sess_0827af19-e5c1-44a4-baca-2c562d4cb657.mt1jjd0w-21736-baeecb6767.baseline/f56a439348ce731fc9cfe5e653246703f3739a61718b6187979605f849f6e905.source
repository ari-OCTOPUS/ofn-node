#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""otel_setup.py — WP2: OpenTelemetry برای ردگیریِ ارکستراسیون Fugu.

قرارداد (Owner-Cockpit WP2، ۲۰۲۶-۰۸-۰۸):
  · Tracer سبک: هر call به Fugu یک span می‌سازد با trace_id.
  · خروجی: traces.jsonl (JSON-lines) — بدون وابستگیِ سنگین به OTel SDK.
  · هر span: trace_id, span_id, parent_id, name, start_ms, end_ms,
    attributes (model, usage, cost, status, error).
  · پشت فلگ OCTOPUS_WIRE_OTEL (default OFF = no-op).

چرا JSON-lines نه OTel collector?
  solo builder — collector جدا overhead دارد. JSON-lines را grep/python
  می‌توان parse کرد و بعداً به Jaeger/Tempo منتقل کرد.
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS) not in sys.path:
    sys.path.insert(0, str(_OPS))

FLAG = "OCTOPUS_WIRE_OTEL"
TRACES_FILE = _OPS / "state" / "otel" / "traces.jsonl"


def _flag_on() -> bool:
    return str(os.environ.get(FLAG, "0")).strip().lower() in ("1", "true", "yes", "on")


def _gen_id() -> str:
    return uuid.uuid4().hex[:16]


class Span:
    """یک spanِ OTel-style — start/end + attributes."""

    def __init__(self, name: str, trace_id: str | None = None,
                 parent_id: str | None = None):
        self.name = name
        self.trace_id = trace_id or _gen_id()
        self.span_id = _gen_id()
        self.parent_id = parent_id
        self.start_ms = int(time.time() * 1000)
        self.end_ms: int | None = None
        self.attributes: dict = {}
        self.status = "ok"
        self.error: str = ""

    def set_attr(self, key: str, value):
        self.attributes[key] = value

    def set_error(self, error: str):
        self.status = "error"
        self.error = error[:200]

    def finish(self):
        self.end_ms = int(time.time() * 1000)
        if _flag_on():
            self._write()

    def _write(self):
        """span را به traces.jsonl بنویس (atomic append با fsync)."""
        try:
            TRACES_FILE.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "parent_id": self.parent_id,
                "name": self.name,
                "start_ms": self.start_ms,
                "end_ms": self.end_ms,
                "duration_ms": (self.end_ms or self.start_ms) - self.start_ms,
                "status": self.status,
                "error": self.error,
                "attributes": self.attributes,
            }
            line = json.dumps(record, ensure_ascii=False) + "\n"
            with open(TRACES_FILE, "a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
        except OSError:
            pass  # telemetry هرگز caller را نمی‌کشد

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.set_error(f"{exc_type.__name__}: {exc_val}")
        self.finish()
        return False  # don't suppress


def start_span(name: str, **attrs) -> Span:
    """شروعِ یک span جدید. با context manager استفاده شود:
    with start_span("fugu.call", model="fugu-ultra") as span:
        ...
    """
    span = Span(name)
    for k, v in attrs.items():
        span.set_attr(k, v)
    return span


def read_traces(limit: int = 100) -> list[dict]:
    """آخرین N span را بخوان (برای dashboard/debug)."""
    try:
        if not TRACES_FILE.exists():
            return []
        lines = TRACES_FILE.read_text("utf-8", errors="replace").splitlines()
        out = []
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
        return out
    except OSError:
        return []
