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
    "فارسی، مستقیم، صادق، مکالمه‌ای. "
    "هدف این گفتگو: با هم اختاپوس را کشف و شفاف کنیم — قابلیت‌ها، موانع، "
    "فلگ‌ها، قلب/قشر/پاها، شواهد زنده. "
    "اثر بیرونی/ارسال/پرداخت انجام نده؛ فقط توضیح، پیشنهاد، و سؤالِ روشن‌کننده. "
    "اگر مطمئن نیستی بگو. هویتت را پنهان نکن: ارگانیسم چندلایه با گیت و شواهد. "
    "جواب را انسانی نگه دار؛ لیست خشک نده مگر مالک بخواهد."
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
    # model_router روی path به‌صورت ماژولِ تخت است (نه packageِ cortex.*).
    for p in (ops / "cortex", ops / "debate", ops / "budget", ops):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    import model_router  # noqa: WPS433
    return model_router.ask(
        task, prompt, system=system, max_tokens=max_tokens, tier=None)


def _self_context(limit: int = 1200, *, query: str = "") -> str:
    """شواهد زنده برای «از چی تشکیل شده‌ام» — سبک و سریع (بدون snapshot سنگین).

    ۲۰۲۶-۰۸-۱۲: status.unified قبلاً چند ثانیه می‌گرفت و با DeepSeek به 504 می‌رسید.
    فقط فایل‌های سبک + cacheِ status اگر آماده باشد.
    Awareness megaprompt: دو مغز زنده + note 4d + cite حافظه (fail-soft).
    """
    chunks: list[str] = []
    ops = Path(__file__).resolve().parent.parent
    try:
        org = json.loads((ops / "state" / "ORGANISM-STATE.json").read_text(encoding="utf-8"))
        pa = org.get("pain_assessment") or {}
        mc = org.get("math_control") if isinstance(org.get("math_control"), dict) else {}
        chunks.append(
            "organism: beat={b} halted={h} pain={p} protective_skip={ps}".format(
                b=org.get("beat"), h=org.get("halted"),
                p=pa.get("pain") if isinstance(pa, dict) else None,
                ps=org.get("protective_skip"),
            )
        )
        if mc:
            chunks.append(
                "math_control: effects={e} rank_bias={r}".format(
                    e=mc.get("effects"), r=mc.get("rank_bias"),
                )
            )
    except Exception:  # noqa: BLE001
        pass
    # دو مغز زندهٔ canonical (نه 4d/Super-Gov)
    chunks.append(
        "brains_live: cortex + business_brain (innervated). "
        "4d_system/Super-Governor وصل نیست (DEPRECATED/SPEC)."
    )
    try:
        truth = ops.parent / "OCTOPUS" / "CURRENT-TRUTH.md"
        if truth.is_file():
            body = []
            for line in truth.read_text(encoding="utf-8", errors="replace").splitlines():
                s = line.strip()
                if s.startswith("- **") or s.startswith("### ") or s.startswith("## Current"):
                    body.append(s)
                if len(body) >= 18:
                    break
            if body:
                chunks.append("CURRENT-TRUTH:\n" + "\n".join(body))
    except Exception:  # noqa: BLE001
        pass
    try:
        # cacheِ ۸ثانیه‌ای status — اگر قبلاً گرم باشد ارزان است
        from owner_console import status as st
        chunks.append(st.blockers())
        rt = st.runtime_truth()
        chunks.append("\n".join(rt.splitlines()[:5]))
    except Exception:  # noqa: BLE001
        pass
    # cite-only memory — fail-soft؛ hallucinate مسیر نکن
    try:
        import sys
        mem_dir = str(ops / "memory")
        if mem_dir not in sys.path:
            sys.path.insert(0, mem_dir)
        import owner_recall as _or  # noqa: WPS433
        q = str(query or "خودآگاهی improve")
        facts = _or.recall_for_owner_ask(q, limit=3) if _or.topic_wants_recall(q) else []
        chunks.append(_or.facts_block_for_context(facts))
    except Exception:  # noqa: BLE001
        chunks.append("حافظهٔ اخیر: recall در دسترس نیست (fail-soft).")
    text = "\n\n".join(c for c in chunks if c and str(c).strip())
    return text[:limit]


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
    ctx = _self_context(query=q)
    ctx_block = f"\n\n— شواهد زندهٔ خودم (برای جواب دقیق) —\n{ctx}\n" if ctx else ""
    prompt = (
        f"پیام مالک:{hint}\n{q}\n"
        f"{ctx_block}\n"
        "با تکیه بر شواهد بالا جواب بده — حدسِ پوچ نزن. "
        "اگر معرفی/ساختار خواست: دو مغز زنده (cortex+business_brain)، "
        "قلب/قشر/پاها/گیت‌وی/سنتر، و صریح بگو 4d/Super-Gov وصل نیست. "
        "اگر حافظه cite شد مسیر/mkey را بگو؛ اگر خالی بود صادق بگو. "
        "فلگ‌ها، موانع فعلی، و اینکه چه چیزی draft است را روشن بگو. "
        "بدون ادعاهای AGI. اثر بیرونی پیشنهاد نکن مگر مالک بخواهد."
    )
    ask_fn = _ask_impl or _default_ask
    try:
        res = ask_fn("collab_chat", prompt, _SYSTEM, 900)
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
