#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""owner_digest.py — جمع‌بندیِ روزانهٔ مالک: مغز digestِ موجود را خلاصه می‌کند (جایگزینِ قالبِ خام).

اتصالِ ۴ از CORTEX-CONNECT-ALL. seamِ واقعی:
  producer → wiring.brain_digest_beat / doctor_digest_beat (متنِ d["text"] پیش از
             _send_stream(channel, …)). splice: d["text"] = owner_digest.summarize(d["text"])["text"]
             — خارج از این لِین (گیت؛ تغییرِ رفتارِ ارسالِ زنده).
  storage  → STATE_DIR/cortex/digest-summaries.jsonl (sha ِ ورودی/خروجی، نه متن).
fallback: مغز نداد ⇒ **همان متنِ خام** برمی‌گردد (fallback=True) — digest هرگز گم نمی‌شود.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _p in (_HERE.parent, _HERE.parent / "budget", _HERE.parent / "cortex"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import opslib      # noqa: E402
import brain_link  # noqa: E402

TASK = "owner_digest"
MAX_TOKENS = 500
SCHEMA = "owner_digest.v1"
_SYSTEM = ("Summarise this daily operations digest for the owner in Persian (فارسی), "
           "max 6 bullet lines, each starting with '▸'. Keep every number exactly as given; "
           "never invent numbers. First line = the single most important item.")


def _sha(s) -> str:
    return hashlib.sha256(str(s or "").encode("utf-8")).hexdigest()[:16]


def summarize(raw_text: str, *, max_chars: int = 900, ask_fn=None, now=None) -> dict:
    raw = str(raw_text or "").strip()
    if not raw:
        return {"ok": False, "reason": "empty-digest", "text": "", "fallback": True}
    r = brain_link.ask_brain(TASK, raw[:6000], system=_SYSTEM,
                             max_tokens=MAX_TOKENS, ask_fn=ask_fn, now=now)
    text = str(r.get("text") or "").strip() if r.get("ok") else ""
    fallback = not text
    out = raw if fallback else text[:max_chars]
    row = {"ts": opslib.now_iso(), "schema": SCHEMA, "task": TASK,
           "ok": bool(r.get("ok")), "fallback": fallback,
           "reason": "" if not fallback else str(r.get("reason") or "no-text"),
           "in_sha": _sha(raw), "in_chars": len(raw), "out_sha": _sha(out), "out_chars": len(out),
           "model": str(r.get("model") or "")[:40] if r.get("ok") else ""}
    try:
        opslib.append_jsonl(opslib.STATE_DIR / "cortex" / "digest-summaries.jsonl", row)
    except Exception:  # noqa: BLE001
        pass
    return {"ok": not fallback, "text": out, "fallback": fallback,
            "reason": row["reason"], "task": TASK}
