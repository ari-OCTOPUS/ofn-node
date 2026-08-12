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


def _self_context(limit: int = 2000, *, query: str = "") -> str:
    """شواهد زنده برای «از چی تشکیل شده‌ام» — سبک و سریع (بدون snapshot سنگین).

    ۲۰۲۶-۰۸-۱۲: status.unified قبلاً چند ثانیه می‌گرفت و با DeepSeek به 504 می‌رسید.
    فقط فایل‌های سبک + cacheِ status اگر آماده باشد.
    لایهٔ ۵ (مغزهای داخلی) از طریق brain_pulse فایل‌خوان به چت می‌آید — نه IPC.
    """
    chunks: list[str] = []
    ops = Path(__file__).resolve().parent.parent
    try:
        org_p = ops / "state" / "ORGANISM-STATE.json"
        org = json.loads(org_p.read_text(encoding="utf-8"))
        pa = org.get("pain_assessment") or {}
        mc = org.get("math_control") if isinstance(org.get("math_control"), dict) else {}
        # 2026-08-12 fix: org["halted"] خودش قابل‌اعتماد نیست — organism.py
        # حتی با STOP-ORGANISM روشن گاهی halted=null می‌نویسد چون
        # opslib.halted() آن فلگِ خاص را چک نمی‌کند (شکافِ مستندشده در
        # opslib.py، پشتِ فلگِ پیش‌فرض-خاموشِ OCTOPUS_WIRE_KILL_SEAM). اینجا
        # مستقیم از دیسک، مستقل از محتوای خودِ فایل، چک می‌شود؛ سنِ فایل هم
        # به مدل داده می‌شود تا beatِ کهنه به‌جای تازه دیده نشود.
        stopped = [n for n in ("STOP-ORGANISM", "STOP-CORTEX", "HALT-ALL")
                   if (ops / n).exists()]
        age_s = time.time() - org_p.stat().st_mtime
        flag_note = (" ⚠️STOPPED[" + ",".join(stopped) + "]") if stopped else ""
        chunks.append(
            "organism: beat={b} halted={h} pain={p} protective_skip={ps} "
            "age={age}s{flag}".format(
                b=org.get("beat"), h=org.get("halted"),
                p=pa.get("pain") if isinstance(pa, dict) else None,
                ps=org.get("protective_skip"),
                age=int(age_s), flag=flag_note,
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
    chunks.append(
        "brains_live: cortex(:8772) + business_brain — innervated در ارگانیسم؛ "
        "به چت با file-bridge وصل‌اند (نه سوکت). "
        "4d_system/Super-Governor وصل نیست (DEPRECATED/SPEC)."
    )
    # لایهٔ ۵ → چت: cortex-state / business-brain / identities / doctor SK
    try:
        import sys
        mem_dir = str(ops / "memory")
        if mem_dir not in sys.path:
            sys.path.insert(0, mem_dir)
        import brain_pulse as _bp  # noqa: WPS433
        _bp.STATE_DIR = ops / "state"
        block = _bp.as_context_block(limit=900)
        if block:
            chunks.append(block)
    except Exception:  # noqa: BLE001
        chunks.append("brain_pulse: unavailable (fail-soft)")
    # OWNER-GOAL (2026-08-12 reconcile): هدفِ قفل‌شدهٔ GOALS-OCTOPUS.md —
    # جهت، نه ادعای قابلیت. invariant صداقت: بدون ادعای AGI/consciousness
    # (OCTOPUS/ARCHITECTURE-BIBLE.md:49-51 · registry.yaml:18 · discovery.py).
    try:
        og = json.loads((ops / "state" / "owner-goal.json").read_text(encoding="utf-8"))
        chunks.append(
            "OWNER-GOAL (GOALS-OCTOPUS.md): هدفِ سنجش‌پذیرِ ماه = "
            + str(og.get("measurable_goal_month") or "")[:170]
            + " — جهت‌های عمومی: خودتحلیل/ارتقا تا حد امن · حافظهٔ ماندگار · "
            "مغزهای موازی · خرجِ گزارش‌پذیر. جهت است نه ادعای قابلیت؛ "
            "بدون ادعای AGI/consciousness.")
    except Exception:  # noqa: BLE001
        pass
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
    # فاز S — session memory (موقت): مکالمهٔ اخیر را به مدل بده
    try:
        import sys
        mem_dir = str(ops / "memory")
        if mem_dir not in sys.path:
            sys.path.insert(0, mem_dir)
        import session_memory as _sm  # noqa: WPS433
        block = _sm.as_context_block(limit=6)
        if block:
            chunks.append(block)
    except Exception:  # noqa: BLE001
        pass
    # فاز W — Context Engine: tiktoken budget management
    try:
        import sys as _csys
        _cog = str(ops / "cognitive")
        if _cog not in _csys.path:
            _csys.path.insert(0, _cog)
        import context_engine as _ce  # noqa: WPS433
        # فقط budget info را به chunks اضافه کن (context_text خودش بعد از complete ساخته می‌شود)
        # اینجا فقط tiktoken availability را چک می‌کنیم
        if _ce._TIKTOKEN is not None:
            chunks.append("context_engine: tiktoken active — budget managed")
    except Exception:  # noqa: BLE001
        pass
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

    # فاز T: Context Engine — context را با tiktoken budget مدیریت کن
    context_info = None
    try:
        import sys as _csys
        from pathlib import Path as _Pce
        _cog = str(_Pce(__file__).resolve().parent.parent / "cognitive")
        if _cog not in _csys.path:
            _csys.path.insert(0, _cog)
        import context_engine as _ce  # noqa: WPS433
        # session turns برای recent_chat
        _turns = []
        try:
            _mem_dir = str(_Pce(__file__).resolve().parent.parent / "memory")
            if _mem_dir not in _csys.path:
                _csys.path.insert(0, _mem_dir)
            import session_memory as _sm  # noqa: WPS433
            _turns = _sm.recent(limit=6)
        except Exception:  # noqa: BLE001
            pass
        # recall facts برای retrieved_memory
        _facts = []
        try:
            import owner_recall as _or  # noqa: WPS433
            if _or.topic_wants_recall(q):
                _facts = _or.recall_for_owner_ask(q, limit=3)
        except Exception:  # noqa: BLE001
            pass
        context_info = _ce.assemble(
            q, intent=kind_hint or "chat",
            session_turns=_turns,
            recall_facts=_facts,
            self_context=_self_context(query=q),
        )
        ctx = context_info["context_text"]
        _budget_used = context_info["token_count"]
    except Exception:  # noqa: BLE001 — fail-soft به مسیر قدیمی
        ctx = _self_context(query=q)

    ctx_block = f"\n\n— شواهد زندهٔ خودم (برای جواب دقیق) —\n{ctx}\n" if ctx else ""
    prompt = (
        f"پیام مالک:{hint}\n{q}\n"
        f"{ctx_block}\n"
        "با تکیه بر شواهد بالا جواب بده — حدسِ پوچ نزن. "
        "اگر معرفی/ساختار خواست: لایه‌ها را صادق بگو — "
        "Reactor/intent → مدل → شواهد فایل → حافظه cite-only → "
        "مغزهای داخلی (cortex+business_brain) که از فایل خوانده شده‌اند "
        "(file-bridge؛ مغزها حرف این چت را مستقیم نمی‌شنوند مگر owner_guidance). "
        "4d/Super-Gov وصل نیست. اعداد cycle/coherence/beat/proposals را از شواهد بگو. "
        "OWNER-GOAL جهت است نه مدرکِ قابلیت فعلی؛ ادعای «الان AGI کامل هستم» نکن. "
        "SoT صداقت: _ops/OCTOPUS-HONESTY.md — لایه‌ها سؤال مهندسی‌اند نه consciousness. "
        "اگر حافظه cite شد مسیر/mkey را بگو. اثر بیرونی پیشنهاد نکن مگر مالک بخواهد."
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
    result = {
        "ok": True,
        "text": text[:4000],
        "model_source": source,
        "tier": tier,
        "model": model,
        "cost_usd": float(res.get("cost_usd") or 0.0),
    }
    # فاز T: context budget info در خروجی (برای observability)
    if context_info:
        result["context_tokens"] = context_info["token_count"]
        result["context_budget"] = context_info["budget_used"]
        result["context_truncated"] = context_info["truncated"]
    return result
