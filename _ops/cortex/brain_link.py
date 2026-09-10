#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""brain_link.py — درِ واحدِ اتصال‌های مغز به model_router (CORTEX-CONNECT-ALL، ۲۰۲۶-۰۹-۱۰).

هر چهار اتصال (پیامِ مشتری · غربالِ لید · پیش‌نویسِ محتوا · digestِ مالک) فقط از
همین در می‌گذرند. این ماژول **هیچ** providerی را مستقیم صدا نمی‌زند: تنها
`model_router.ask` (→ TASK_TIERS → گیت‌های پولی → client → لجرِ paid-calls.jsonl).

قواعدِ آهنین:
  · اسکرابرِ راز (cortex/scrub.py) روی prompt و system، **پیش از** فراخوانی و پیش از لاگ.
  · task صریح در هر فراخوانی؛ tier صریح (پیش‌فرض secondary = مغزِ پولی؛ task ِ
    ناشناخته در TASK_TIERS به local می‌افتد و این عمداً با tier صریح دور زده می‌شود).
  · سقفِ روزانهٔ **اضافه** بر گیت‌های fugu (نه به‌جای آن‌ها): connect-daily.json.
  · None / خطا / dict ِ ناموفق / پاسخِ بریدهٔ بی‌متن (is_useless_truncation) /
    متنِ خالی / مغزِ غیرپولی → {"ok": False, "reason": …}. صداکننده fallback می‌دهد.
  · رسیدِ هر فراخوانی در connect-calls.jsonl: task/ok/reason/chars_out/sha — هرگز
    متنِ prompt یا پاسخ. لجرِ پولیِ واقعی را خودِ model_router می‌نویسد.

transport جعلی برای تست: `ask_fn=` تزریق می‌شود؛ شبکه صفر.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent            # _ops/cortex
for _p in (_HERE, _HERE.parent, _HERE.parent / "budget"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import opslib  # noqa: E402
import scrub   # noqa: E402

PAID_TIERS = ("primary", "secondary")
DEFAULT_TIER = "secondary"
DEFAULT_DAILY_CAP = 20
RECEIPTS = "connect-calls.jsonl"
DAILY = "connect-daily.json"


def _state_dir() -> Path:
    return opslib.STATE_DIR / "cortex"


def _sha(text) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


def _today(now: float | None = None) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(now if now is not None else time.time()))


def daily_cap(task: str) -> int:
    """سقفِ روزانهٔ این اتصال: OCTOPUS_CONNECT_DAILY_CAP_<TASK> → OCTOPUS_CONNECT_DAILY_CAP → ۲۰."""
    key = "OCTOPUS_CONNECT_DAILY_CAP_" + str(task or "").upper().replace("-", "_").replace(".", "_")
    for name in (key, "OCTOPUS_CONNECT_DAILY_CAP"):
        raw = os.environ.get(name, "")
        if raw.strip():
            try:
                return max(0, int(raw))
            except ValueError:
                continue
    return DEFAULT_DAILY_CAP


def _daily_reserve(task: str, cap: int, now: float | None = None) -> tuple[bool, int]:
    """attempt-counted (همان فلسفهٔ fugu_quota.reserve): +۱ **قبل** از تماس.
    I/O شکست → fail-closed (اجازه نه)."""
    p = _state_dir() / DAILY
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        st = json.loads(p.read_text("utf-8")) if p.exists() else {}
        if not isinstance(st, dict) or st.get("date") != _today(now):
            st = {"date": _today(now), "counts": {}}
        counts = st.setdefault("counts", {})
        used = int(counts.get(task, 0))
        if used >= cap:
            return False, used
        counts[task] = used + 1
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(st, ensure_ascii=False), "utf-8")
        os.replace(tmp, p)
        return True, used + 1
    except Exception:  # noqa: BLE001 — fail-closed
        return False, -1


def _receipt(row: dict) -> None:
    try:
        opslib.append_jsonl(_state_dir() / RECEIPTS, row)
    except Exception:  # noqa: BLE001 — رسید هرگز مسیر را نمی‌کشد
        pass


def ask_brain(task: str, prompt: str, *, system: str = "", max_tokens: int = 600,
              tier: str = DEFAULT_TIER, ask_fn=None, cap: int | None = None,
              now: float | None = None) -> dict:
    """یک پرسش از مغزِ پولی، با اسکرابر + سقف + اعتبارسنجیِ پاسخ + رسید.

    خروجی همیشه dict: {"ok": bool, "task", "reason"?, "text"?, "tier"?, "model"?}.
    هرگز استثنا بیرون نمی‌دهد. متنِ prompt/پاسخ هرگز لاگ نمی‌شود."""
    task = str(task or "").strip() or "unknown"
    p_clean = scrub.scrub(prompt)
    s_clean = scrub.scrub(system)
    base = {"ts": opslib.now_iso(), "task": task, "tier": tier,
            "prompt_sha": _sha(p_clean), "prompt_chars": len(p_clean),
            "scrubbed": bool(scrub.leaks(prompt) or scrub.leaks(system))}

    _cap = daily_cap(task) if cap is None else int(cap)
    allowed, used = _daily_reserve(task, _cap, now)
    if not allowed:
        _receipt({**base, "ok": False, "reason": "connect-daily-cap", "used": used, "cap": _cap})
        return {"ok": False, "task": task, "reason": "connect-daily-cap", "used": used, "cap": _cap}

    if ask_fn is None:
        try:
            import model_router as _mr   # noqa: WPS433 — lazy؛ تنها درِ مجاز
            ask_fn = _mr.ask
        except Exception as e:  # noqa: BLE001
            _receipt({**base, "ok": False, "reason": f"router-unavailable:{type(e).__name__}"})
            return {"ok": False, "task": task, "reason": f"router-unavailable:{type(e).__name__}"}

    try:
        r = ask_fn(task, p_clean, system=s_clean, max_tokens=int(max_tokens), tier=tier)
    except Exception as e:  # noqa: BLE001 — timeout/شبکه/هرچه
        _receipt({**base, "ok": False, "reason": f"ask-exception:{type(e).__name__}"})
        return {"ok": False, "task": task, "reason": f"ask-exception:{type(e).__name__}"}

    if not isinstance(r, dict):
        _receipt({**base, "ok": False, "reason": "no-answer"})
        return {"ok": False, "task": task, "reason": "no-answer"}
    if not r.get("ok"):
        why = str(r.get("reason") or "no-answer")[:60]
        _receipt({**base, "ok": False, "reason": why})
        return {"ok": False, "task": task, "reason": why}
    got_tier = str(r.get("tier") or "")
    if r.get("fallback_from") or (got_tier and got_tier not in PAID_TIERS):
        _receipt({**base, "ok": False, "reason": "not-a-paid-brain", "got_tier": got_tier[:16]})
        return {"ok": False, "task": task, "reason": "not-a-paid-brain", "got_tier": got_tier}
    text = str(r.get("text") or "").strip()
    try:
        import model_router as _mr2   # noqa: WPS433
        burned = _mr2.is_useless_truncation(text, r.get("finish_reason"))
    except Exception:  # noqa: BLE001 — همان منطق، بدونِ وابستگی به import
        burned = (r.get("finish_reason") == "length" and len(text) < 40)
    if burned:
        _receipt({**base, "ok": False, "reason": "useless-truncation", "chars_out": len(text)})
        return {"ok": False, "task": task, "reason": "useless-truncation"}
    if not text:
        _receipt({**base, "ok": False, "reason": "empty"})
        return {"ok": False, "task": task, "reason": "empty"}
    # پاسخِ مدل هم از اسکرابر می‌گذرد: مدل نباید بتواند رازی را «بازتاب» دهد.
    text = scrub.scrub(text)
    _receipt({**base, "ok": True, "chars_out": len(text), "out_sha": _sha(text),
              "model": str(r.get("model") or "")[:40], "got_tier": got_tier[:16]})
    return {"ok": True, "task": task, "text": text, "tier": got_tier,
            "model": r.get("model"), "finish_reason": r.get("finish_reason")}
