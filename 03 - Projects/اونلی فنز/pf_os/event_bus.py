#!/usr/bin/env python3
"""event_bus.py — 🧠⚡ سیستمِ عصبیِ nodeِ Project-F (gapِ #۱ در OCTOPUS-ACTUATION-ALIGNMENT §۳.۱).

قبلاً: handoff فقط file-based بود (`.json`/`.md`) — بدونِ correlation، بدونِ health،
بدونِ pub/sub. این ماژول همان `event_bus.py` سفارش‌شده در §۵.۱ است:

  • envelope مطابقِ `_ops/log-event-v1.schema.json` (v/ts/level/event/msg/organ/trace/span/status)
  • نام‌گذاری قفل‌شده‌ی taxonomy: `organ.domain.action` (event-taxonomy-v1)
  • trace (16-hex) + span (8-hex) + parent → زنجیره‌ی علّی قابلِ بازسازی
  • JSONL per-topic زیرِ `PF_STATE/.bus/` + `all.jsonl` (append-only)
  • subscribe advisory (هم‌الگوی `_ops/unified_bus.py` W-2: مشترکِ خراب bus را نمی‌کشد)
  • mirror اختیاری و fail-soft به loggerِ مرکزیِ `_ops/events.py` (فقط ۷ نامِ legacy)
  • health(): last-seen / error-rate هر organ — پاسخ به «کدام بازو کند/مرده است؟»

containment: هرگز PII/محتوا در msg/payload نمی‌رود؛ scrub هم‌ارزِ `_ops/events.py::_BANNED_ECHO`.
$0 · stdlib-only · fail-soft در مصرف، fail-closed در اعتبارسنجی.
"""
from __future__ import annotations

import contextvars
import datetime as _dt
import json
import os
import re
import secrets
import time
from pathlib import Path
from typing import Callable, Optional

from . import config
from . import events as central_events

# ─── قراردادِ envelope (log-event-v1) ────────────────────────────────────────
SCHEMA_V = "1.0.0"
LEVELS = frozenset({"DEBUG", "INFO", "WARN", "ERROR", "CRIT"})
STATUSES = frozenset({"started", "success", "failed", "blocked",
                      "retrying", "skipped", "unknown"})
APPROVAL = frozenset({"required", "approved", "denied", "not_required",
                      "pending", "unknown"})
_EVENT_RE = re.compile(r"^[a-z]+\.[a-z]+\.[a-z_]+$")

# containment parity با _ops/events.py (هیچ رشته‌ی ممنوع echo نمی‌شود)
# دوزبانه (لِین B · 2026-08-03): «اونلی» شکل‌های «اونلی فنز/اونلی‌فنز» را هم
# می‌گیرد، ولی املای بدونِ واو و نامِ پلتفرمِ دوم به فارسی از فهرست بیرون بودند.
_BANNED_ECHO = ("اونلی", "onlyfans", "صبا", "انلی فنز", "فنسلی")

# نگاشتِ ۱:۱ ی/ک عربی → فارسی. عمداً **بدونِ** حذفِ نیم‌فاصله/کشیده، چون این
# تابع باید طولِ رشته را حفظ کند تا آفست‌های `norm` روی `out` معتبر بمانند.
_FA_CHARS = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک"})

# نگاشتِ رویدادِ taxonomy → ۷ نامِ legacyِ loggerِ مرکزی (fail-soft mirror)
_LEGACY_MAP = {
    "started": "task.started", "success": "task.completed",
    "failed": "task.failed", "blocked": "task.blocked",
}

# trace جاری (contextvars — هم‌الگوی correlation_id در pf_os/events.py)
_trace_var: contextvars.ContextVar[str] = contextvars.ContextVar("pf_trace", default="")
_span_var: contextvars.ContextVar[str] = contextvars.ContextVar("pf_span", default="")


def _scrub(text: str) -> str:
    """حذفِ رشته‌های ممنوع از هر خروجی (containment). fail-soft.

    دو پاس: (۱) تحت‌اللفظی — همان رفتارِ قبلی، بایت‌به‌بایت؛ (۲) روی شکلِ نرمالِ
    **هم‌طول** (ی/ک عربی → فارسی) تا «اونلي» هم مثلِ «اونلی» گرفته شود.
    چرا هم‌طول: خروجیِ این تابع در `make_event` به `json.loads` داده می‌شود، پس
    نه می‌شود کلِ رشته را redact کرد (JSON خراب می‌شود) و نه طول را به‌هم زد؛
    نگاشت ۱:۱ آفست‌ها را معتبر نگه می‌دارد. متنِ پاک دست‌نخورده برمی‌گردد.
    """
    out = str(text)
    for b in _BANNED_ECHO:
        if b and b in out:
            out = out.replace(b, "▇")
    norm = out.translate(_FA_CHARS)
    for b in _BANNED_ECHO:
        bn = b.translate(_FA_CHARS)
        while bn and bn in norm:
            i = norm.index(bn)
            out = out[:i] + "▇" + out[i + len(bn):]
            norm = out.translate(_FA_CHARS)
    return out


def new_trace() -> str:
    """شروعِ یک زنجیره‌ی علّیِ جدید. trace را در context ست می‌کند و برمی‌گرداند."""
    t = secrets.token_hex(8)          # 16 hex chars
    _trace_var.set(t)
    _span_var.set("")
    return t


def current_trace() -> str:
    return _trace_var.get() or new_trace()


def make_event(event: str, organ: str, msg: str, *, status: str = "success",
               level: str = "INFO", agent_id: str | None = None,
               approval_state: str = "not_required",
               duration_ms: int | None = None, gate_name: str | None = None,
               gate_reason: str | None = None, payload: dict | None = None,
               tags: list[str] | None = None) -> dict:
    """ساختِ envelope معتبر طبقِ log-event-v1. اعتبارسنجی fail-closed:
    نامِ خارج از الگوی taxonomy یا status/level ناشناخته → ValueError."""
    if not _EVENT_RE.match(event):
        raise ValueError(f"event name violates taxonomy organ.domain.action: {event!r}")
    if level not in LEVELS:
        raise ValueError(f"unknown level: {level!r}")
    if status not in STATUSES:
        raise ValueError(f"unknown status: {status!r}")
    if approval_state not in APPROVAL:
        raise ValueError(f"unknown approval_state: {approval_state!r}")
    parent = _span_var.get() or None
    span = secrets.token_hex(4)       # 8 hex chars
    _span_var.set(span)
    ev = {
        "v": SCHEMA_V,
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "level": level,
        "event": event,
        "msg": _scrub(msg)[:512] or "-",
        "organ": organ,
        "agent_id": agent_id,
        "trace": current_trace(),
        "span": span,
        "parent": parent,
        "status": status,
        "approval_state": approval_state,
        "duration_ms": int(duration_ms) if duration_ms is not None else None,
        "gate_name": gate_name,
        "gate_reason": _scrub(gate_reason)[:200] if gate_reason else None,
        "tags": [_scrub(t) for t in (tags or [])],
        "p": json.loads(_scrub(json.dumps(payload or {}, ensure_ascii=False))),
    }
    return ev


class EventBus:
    """bus سبکِ per-node: append-only JSONL + مشترک‌های advisory + health.

    نوشتن: `PF_STATE/.bus/<organ>.jsonl` + `PF_STATE/.bus/all.jsonl`
    مصرف: subscribe (advisory، فقط اطلاع) یا replay (خواندنِ تاریخچه).
    هیچ مشترکی effect بیرونی ندارد — actuation فقط از مسیرِ actuator (gated).
    """

    def __init__(self, state_dir: str | Path | None = None,
                 mirror_central: bool = True):
        base = Path(state_dir) if state_dir else Path(config.ensure_pf_state())
        self.dir = base / ".bus"
        self.dir.mkdir(parents=True, exist_ok=True)
        self._subs: list[tuple[Optional[str], Callable]] = []
        self._mirror = mirror_central

    # ── publish ──
    def publish(self, event: str, organ: str, msg: str, **kw) -> dict:
        """ساخت + اعتبارسنجی + append + notify + mirror. خروجی: envelope ثبت‌شده."""
        ev = make_event(event, organ, msg, **kw)
        line = json.dumps(ev, ensure_ascii=False)
        for fname in (f"{organ}.jsonl", "all.jsonl"):
            try:
                with open(self.dir / fname, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except OSError:
                pass                      # fail-soft: دیسک نباید حلقه را بکشد
        self._notify(ev)
        if self._mirror:
            self._mirror_central(ev)
        return ev

    def safe_publish(self, event: str, organ: str, msg: str, **kw) -> dict | None:
        """publish که هرگز raise نمی‌کند (برای مسیرهای داغِ حلقه). None = دورانداخته."""
        try:
            return self.publish(event, organ, msg, **kw)
        except Exception:  # noqa: BLE001
            return None

    # ── subscribe (advisory — W-2 هم‌الگوی unified_bus) ──
    def subscribe(self, callback: Callable, event_prefix: str | None = None) -> None:
        """callback(event_dict). event_prefix=None یعنی همه؛ وگرنه startswith."""
        self._subs.append((event_prefix, callback))

    def _notify(self, ev: dict) -> None:
        name = ev.get("event", "")
        for prefix, cb in self._subs:
            if prefix is None or name.startswith(prefix):
                try:
                    cb(ev)
                except Exception:  # noqa: BLE001 — مشترکِ خراب bus را نمی‌کشد
                    pass

    # ── mirror به loggerِ مرکزی (fail-soft؛ فقط اگر _ops در scope باشد) ──
    def _mirror_central(self, ev: dict) -> None:
        legacy = _LEGACY_MAP.get(ev.get("status", ""))
        if not legacy:
            return
        try:
            central_events.emit(legacy, status=ev.get("status", "unknown"),
                                summary=f"{ev['event']}: {ev['msg']}"[:300],
                                duration_ms=ev.get("duration_ms") or 0,
                                approval_state={"not_required": "none"}.get(
                                    ev.get("approval_state", "unknown"),
                                    ev.get("approval_state", "unknown")))
        except Exception:  # noqa: BLE001
            pass

    # ── replay (تاریخچه از دیسک — source of truth همین JSONLهاست) ──
    def replay(self, organ: str | None = None, event_prefix: str | None = None,
               limit: int = 1000) -> list[dict]:
        path = self.dir / (f"{organ}.jsonl" if organ else "all.jsonl")
        out: list[dict] = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if event_prefix and not str(ev.get("event", "")).startswith(event_prefix):
                        continue
                    out.append(ev)
        except OSError:
            return []
        return out[-limit:]

    # ── health — پاسخ به gap «کدام بازو کند/مرده است؟» ──
    def health(self, stale_after_s: float = 900.0) -> dict:
        """per-organ: تعداد، خطا، آخرین ts، و stale بودن (heartbeat age)."""
        now = time.time()
        organs: dict[str, dict] = {}
        for ev in self.replay(limit=5000):
            o = ev.get("organ", "?")
            d = organs.setdefault(o, {"count": 0, "errors": 0, "last_ts": ""})
            d["count"] += 1
            if ev.get("status") in ("failed", "blocked"):
                d["errors"] += 1
            d["last_ts"] = ev.get("ts", d["last_ts"])
        for o, d in organs.items():
            try:
                last = _dt.datetime.fromisoformat(d["last_ts"]).timestamp()
                d["age_s"] = round(now - last, 1)
                d["stale"] = d["age_s"] > stale_after_s
            except (ValueError, TypeError, OSError):
                d["age_s"] = None
                d["stale"] = True
            d["error_rate"] = round(d["errors"] / max(d["count"], 1), 3)
        return organs
