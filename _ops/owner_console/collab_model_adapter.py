#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collab_model_adapter.py — thin bridge: collaborator → model_router.ask.

Fail-closed, injectible for tests. No outbound send. No secrets in return.
Flag gate lives in collaborator._use_model(); this module only executes the call.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Callable

# Daily soft cap (calls). Hard money gating remains in model_router/organ_gate.
COLLAB_DAILY_CAP_ENV = "OCTOPUS_COLLAB_MODEL_DAILY_CAP"
# Owner/runtime invariant (Integration Wave 2026-08-11): Collaborator uses at most
# 20 model-backed turns per UTC day unless an explicit env override is supplied.
# This is independent of the AU$30 monthly money cap.
COLLAB_DAILY_CAP_DEFAULT = 20

_SYSTEM = (
    "تو اختاپوس هستی — مغزِ کنترل و همکارِ مالک (آرمین). "
    "فارسی، مستقیم، صادق. اثر بیرونی/ارسال/پرداخت انجام نده؛ فقط توضیح و پیشنهاد. "
    "اگر مطمئن نیستی بگو. هویتت را پنهان نکن: ارگانیسم چندلایه با گیت و شواهد."
)

# Injectable for unit tests: Callable[[str, str], dict]
_ask_impl: Callable[..., dict] | None = None


def set_ask_impl(fn: Callable[..., dict] | None) -> None:
    """Test seam — replace model_router.ask. Pass None to restore default."""
    global _ask_impl
    _ask_impl = fn


def daily_cap() -> int:
    try:
        return max(1, int(os.environ.get(COLLAB_DAILY_CAP_ENV, COLLAB_DAILY_CAP_DEFAULT)))
    except (TypeError, ValueError):
        return COLLAB_DAILY_CAP_DEFAULT


def _counter_path() -> Path:
    raw = os.environ.get("OCTOPUS_COLLAB_MODEL_COUNTER", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent.parent / "state" / "collab-model-daily.json"


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _load_counter() -> dict:
    path = _counter_path()
    if not path.is_file():
        return {"day": _today(), "count": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"day": _today(), "count": 0}
    if str(data.get("day") or "") != _today():
        return {"day": _today(), "count": 0}
    try:
        count = int(data.get("count") or 0)
    except (TypeError, ValueError):
        count = 0
    return {"day": _today(), "count": max(0, count)}


def _bump_counter() -> int:
    """Increment soft daily call counter; returns new count."""
    path = _counter_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    cur = _load_counter()
    cur["count"] = int(cur.get("count") or 0) + 1
    cur["day"] = _today()
    path.write_text(json.dumps(cur), encoding="utf-8")
    return cur["count"]


def check_daily_cap() -> dict:
    """Soft gate before model call. Does not spend money itself."""
    cur = _load_counter()
    cap = daily_cap()
    used = int(cur.get("count") or 0)
    if used >= cap:
        return {"ok": False, "reason": "daily-cap", "used": used, "cap": cap}
    return {"ok": True, "used": used, "cap": cap}


def _default_ask(task: str, prompt: str, system: str, max_tokens: int) -> dict:
    import sys
    from pathlib import Path
    ops = Path(__file__).resolve().parent.parent
    cortex = str(ops / "cortex")
    if cortex not in sys.path:
        sys.path.insert(0, cortex)
    if str(ops) not in sys.path:
        sys.path.insert(0, str(ops))
    from cortex.model_router import ask  # noqa: WPS433
    return ask(task, prompt, system=system, max_tokens=max_tokens, tier=None)


def complete(owner_text: str, *, kind_hint: str = "") -> dict[str, Any]:
    """Call model for collaborator turn. Returns normalized dict.

    ok=True → text + model_source (tier/model)
    ok=False → reason (never raises)
    """
    q = str(owner_text or "").strip()[:600]
    if not q:
        return {"ok": False, "reason": "empty"}

    gate = check_daily_cap()
    if not gate.get("ok"):
        return {
            "ok": False,
            "reason": "daily-cap",
            "used": gate.get("used"),
            "cap": gate.get("cap"),
        }

    hint = f"\n(context_kind_hint={kind_hint})" if kind_hint else ""
    prompt = (
        f"پیام مالک:{hint}\n{q}\n\n"
        "جواب کوتاه و مفید بده. اگر معرفی خواست، خودت را به‌عنوان اختاپوس "
        "و نقش همکار مالک توضیح بده (گیت‌ها، شواهد، بدون ادعاهای AGI)."
    )
    ask_fn = _ask_impl or _default_ask
    try:
        res = ask_fn("collab_chat", prompt, _SYSTEM, 500)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": type(exc).__name__}

    if not isinstance(res, dict) or not res.get("ok"):
        return {
            "ok": False,
            "reason": (res or {}).get("reason") if isinstance(res, dict) else "no-answer",
            "tier": (res or {}).get("tier") if isinstance(res, dict) else None,
        }
    text = str(res.get("text") or res.get("answer") or "").strip()
    if len(text) < 8:
        return {"ok": False, "reason": "too-short", "tier": res.get("tier")}
    try:
        _bump_counter()
    except OSError:
        pass
    tier = str(res.get("tier") or "local")
    model = str(res.get("model") or "")
    source = f"{tier}:{model}" if model else tier
    return {
        "ok": True,
        "text": text[:4000],
        "model_source": source,
        "tier": tier,
        "model": model,
        "cost_usd": float(res.get("cost_usd") or 0.0),
    }
