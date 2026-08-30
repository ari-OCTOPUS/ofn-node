#!/usr/bin/env python3
"""chat_log.py — سیوِ سرور-ساید گفتگوی مالک (append-only JSONL).

2026-08-12 (owner request): «همرو تو همین وب‌اپ و صحبت با من سیو کن و وصل کن»
قبل از این ماژول، چت فقط در localStorage مرورگر (octopus.asklog.v1) بود و با
clear مرورگر می‌رفت. این ماژول:
  - هر نوبت (مالک + پاسخ) را در state/chat/chat-log.jsonl سیو می‌کند
  - run_id/kind/model_source را نگه می‌دارد تا به Cognitive Runtime وصل باشد
  - redact می‌کند: initData/secret/token هرگز ذخیره نمی‌شوند (دفاع دولایه)
  - fail-soft مطلق: هیچ‌وقت گفتگو را نمی‌کشد

قانون: این فایل فقط LOG است — نه authorize، نه semantic write. may_authorize=false.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

STATE_DIR = Path(__file__).resolve().parent.parent / "state"
CHAT_FILE = STATE_DIR / "chat" / "chat-log.jsonl"

# الگوهای حساس — هرگز سیو نمی‌شوند (فقط جایگزین می‌شوند)
_REDACT_PATTERNS = [
    (re.compile(r"initData[=:][^\s&\"']{0,512}", re.I), "initData=<redacted>"),
    (re.compile(r"query_id[=:][^\s&\"']+", re.I), "query_id=<redacted>"),
    (re.compile(r"(api[_-]?key|token|secret|password)[=:]\s*[\w.\-]{8,}", re.I),
     r"\1=<redacted>"),
]

_SCHEMA = "owner-console.chat-log.v1"


def redact(text: str) -> str:
    """پاک‌سازی رشتهٔ ورودی از secret — قبل از هر ذخیره."""
    if not text:
        return text
    out = str(text)
    for pat, repl in _REDACT_PATTERNS:
        out = pat.sub(repl, out)
    return out[:2000]  # سقف هر نوبت


def append(*, role: str, kind: str, text: str, run_id: str = "",
           model_source: str = "", turn_id: str = "") -> dict:
    """یک نوبت گفتگو را به لاگ چت اضافه کن (fail-soft)."""
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema": _SCHEMA,
        "role": role,            # owner | collaborator
        "kind": kind or "chat",
        "text": redact(text),
        "run_id": run_id or "",
        "model_source": model_source or "",
        "turn_id": turn_id or "",
        "may_authorize": False,
    }
    try:
        CHAT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CHAT_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return {"ok": True, "record": rec}
    except OSError as exc:  # fail-soft
        return {"ok": False, "reason": type(exc).__name__}


def recent(limit: int = 10) -> list[dict]:
    """آخرین N نوبت (نزولی) — برای UI و context."""
    try:
        if not CHAT_FILE.is_file():
            return []
        rows: list[dict] = []
        with CHAT_FILE.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except (ValueError, json.JSONDecodeError):
                    continue
                rows.append(rec)
        return rows[-limit:][::-1]
    except OSError:
        return []


def as_context_block(limit: int = 4) -> str:
    """بلوک متنی آخرین نوبت‌ها برای context مدل (fail-soft)."""
    rows = recent(limit=limit)
    if not rows:
        return ""
    lines = []
    for r in rows:
        who = "مالک" if r.get("role") == "owner" else "اختاپوس"
        body = str(r.get("text") or "").strip().replace("\n", " ")[:160]
        lines.append(f"[{who}]: {body}")
    return "آخرین گفتگو با مالک:\n" + "\n".join(lines)


def count() -> int:
    return len(recent(limit=10 ** 6))


def clear() -> dict:
    """فقط برای تست — لاگ واقعی را پاک نکن مگر با حکم مالک."""
    return {"ok": False, "reason": "manual_only"}
