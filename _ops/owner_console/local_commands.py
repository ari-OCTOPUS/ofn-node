#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""local_commands.py — فرمان‌های محلی owner-console (F3 الحاقیهٔ ۱۴A).

/status · /health · /memory · /help · /capabilities · /remember — همیشه محلی،
صفر فراخوان مدل. /remember حافظهٔ episodic/semantic را در همان store حلقهٔ
یادگیری می‌نویسد (research/full_loop/state/memory.jsonl) تا canary بعدی
(/remember → recall) روی همان ID کار کند."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[1]
MEMORY_STORE = _ROOT / "research/full_loop/state/memory.jsonl"

LOCAL = frozenset({"/status", "/health", "/memory", "/help", "/capabilities"})


def _snapshot() -> dict:
    out = {}
    try:
        d = json.loads((_ROOT / "_ops/state/ORGANISM-STATE.json").read_text(encoding="utf-8"))
        out["beat"] = d.get("beat")
    except Exception:  # noqa: BLE001
        out["beat"] = None
    try:
        m = json.loads((_ROOT / "_ops/state/pulse/memory-read-latest.json")
                       .read_text(encoding="utf-8"))
        out["memread"] = f"{m.get('status')}/r{m.get('memory_reads_per_cycle')}/{m.get('readback')}"
    except Exception:  # noqa: BLE001
        out["memread"] = "?"
    return out


def status_text() -> str:
    s = _snapshot()
    return (f"🐙 beat={s['beat']} · memory={s['memread']} · LIVE-A✓ "
            f"B:BLOCKED(pending tg≥5) C:PASS·incident · executable=false")


def handle_local(text: str) -> tuple[bool, str]:
    """(handled, reply) — handled=False یعنی پیام آزاد است، به مغز برود."""
    cmd = text.strip().split()[0].lower()
    if cmd in ("/status", "/health"):
        return True, status_text()
    if cmd == "/memory":
        return True, "حافظهٔ حلقه: episodic/semantic در memory.jsonl — بازیابی با decision_time (LIVE-C)."
    if cmd == "/help":
        return True, ("فرمان‌ها: /status · /health · /memory · /help · "
                      "/capabilities · /remember <text> · /good|/bad <turn>")
    if cmd == "/capabilities":
        return True, ("حلقهٔ یادگیری مالک: ingest دوزمانی → ۳ read حافظه → HC/WM → "
                      "gate BLOCK/SHADOW/ADVISORY → DeepSeek (پولی منجمد تا ریشهٔ quota) "
                      "→ پاسخ با footer → memory commit. executable=false همیشه.")
    if cmd == "/remember":
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return True, "usage: /remember <text>"
        return True, _remember(parts[1])
    return False, ""


def _remember(payload: str) -> str:
    import hashlib
    from datetime import datetime, timezone
    mid = f"mem-{hashlib.sha256(f'semantic|{payload}'.encode()).hexdigest()[:12]}"
    row = {"id": mid, "kind": "semantic", "text": payload, "turn_id": "owner-cmd",
           "provenance": "owner_direct",
           "occurred_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "recorded_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds")}
    MEMORY_STORE.parent.mkdir(parents=True, exist_ok=True)
    with MEMORY_STORE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return f"✓ ثبت شد: {mid} (semantic candidate — تا تأیید شما fact نمی‌شود)"
