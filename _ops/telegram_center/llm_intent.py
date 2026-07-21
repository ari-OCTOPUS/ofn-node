#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_intent — understand ANY free-text owner request with the bot's own brain (model_router:
local→GLM→Fugu) and turn it into a STRUCTURED mission proposal.

SAFETY (non-negotiable): the LLM only UNDERSTANDS + PROPOSES. It NEVER executes anything.
Execution always stays behind the same gate: mission → autonomy_matrix → owner ✅ card → gated
runner. Defense-in-depth: autonomy_matrix.is_important re-checks the LLM's proposed action, so a
model mis-classification can never lower the gate. Fail-safe: any doubt/parse/LLM failure -> ok=False
(the caller falls back to the rule-based path or asks the owner to clarify — never auto-acts).

Flag: OCTOPUS_TG_LLM_ASK (off by default). Content-free by contract; the caller scrubs before send.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
for _p in (str(_HERE), str(_OPS), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FLAG = "OCTOPUS_TG_LLM_ASK"
_INTENTS = ("status", "revenue", "budget", "leg_action", "code", "research", "mission", "unknown")
_LEGS = ("lead", "ziman", "mining", "crypto", "accounting", "studio_pf", "knowledge", "cartographer")
_RISK = ("low", "medium", "high")

_SYSTEM = (
    "تو مغزِ تشخیصِ نیتِ اختاپوسی. کارِ کاربر را بفهم و فقط یک JSON بده — هیچ متنِ اضافه، هیچ توضیح. "
    "هرگز دستور اجرا نکن؛ فقط توصیف کن که کاربر چه می‌خواهد.\n"
    'قالبِ دقیق: {"intent":"...","target_leg":"...|null","action":"فعلِ کوتاه",'
    '"risk":"low|medium|high","summary":"یک جملهٔ فارسیِ ساده","needs_mission":true|false}\n'
    f"intent یکی از این‌ها: {', '.join(_INTENTS)}. "
    f"target_leg یکی از این‌ها یا null: {', '.join(_LEGS)}. "
    "needs_mission=true یعنی کارِ اجرایی/کدی/تغییری است که باید مأموریت شود."
)


def enabled() -> bool:
    return os.environ.get(FLAG, "0") == "1"


def _extract_json(text: str):
    """Robustly pull the first {...} object out of an LLM reply. None on failure."""
    if not text:
        return None
    m = re.search(r"\{.*\}", str(text), re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:  # noqa: BLE001
        return None


def _is_important(blob: str):
    """autonomy_matrix.is_important as defense-in-depth. Fail-safe -> important (gate)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "autonomy_matrix", str(_OPS / "cortex" / "autonomy_matrix.py"))
        am = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(am)
        return am.is_important({"title": blob, "action": blob})
    except Exception:  # noqa: BLE001
        return True, "fail-safe: autonomy_matrix unavailable"


def understand(text: str, *, ask_fn=None) -> dict:
    """LLM → structured mission proposal. Never executes. Always returns a dict with `ok`.

    ok=False -> caller falls back (rule-based / clarify). ok=True -> a proposal the caller may turn
    into a gated mission. `ask_fn` is injectable (tests); defaults to model_router.ask."""
    text = str(text or "").strip()
    if not text:
        return {"ok": False, "reason": "empty"}
    if ask_fn is None:
        try:
            import model_router  # the bot's brain (local→GLM→Fugu, budget-managed)
            ask_fn = model_router.ask
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "reason": f"router-unavailable:{e.__class__.__name__}"}
    try:
        res = ask_fn("tg_intent", text, system=_SYSTEM, max_tokens=200)
    except Exception as e:  # noqa: BLE001 — never crash the bot on an LLM hiccup
        return {"ok": False, "reason": f"llm-error:{e.__class__.__name__}"}
    if not isinstance(res, dict) or not res.get("ok"):
        return {"ok": False, "reason": "llm-no-answer",
                "detail": res.get("reason") if isinstance(res, dict) else None}
    data = _extract_json(res.get("text"))
    if not isinstance(data, dict):
        return {"ok": False, "reason": "unparseable"}

    intent = data.get("intent") if data.get("intent") in _INTENTS else "unknown"
    leg = data.get("target_leg") if data.get("target_leg") in _LEGS else None
    action = str(data.get("action") or "")[:120]
    summary = str(data.get("summary") or action or text)[:200]
    risk = data.get("risk") if data.get("risk") in _RISK else "medium"
    needs_mission = bool(data.get("needs_mission"))

    # defense-in-depth: the keyword gate re-checks; important -> force high + mission + owner card,
    # even if the model said "low". A mis-classification can only RAISE the gate, never lower it.
    # The RAW owner text is included too, so a model that launders a dangerous request into benign
    # action/summary words cannot dodge the gate-raise (adding text can only raise, never lower).
    important, why = _is_important(f"{action} {summary} {text}")
    if important:
        risk, needs_mission = "high", True

    return {"ok": True, "intent": intent, "target_leg": leg, "action": action,
            "summary": summary, "risk": risk, "needs_mission": needs_mission,
            "important": important, "gate_reason": why if important else "",
            "tier": res.get("tier")}


if __name__ == "__main__":
    # offline smoke with a fake brain (no network)
    def _fake(task, prompt, system="", max_tokens=200):
        return {"ok": True, "tier": "local",
                "text": '{"intent":"code","target_leg":"lead","action":"اجرای تست",'
                        '"risk":"low","summary":"تست‌های تلگرام اجرا شود","needs_mission":true}'}
    print(json.dumps(understand("تست‌ها رو اجرا کن", ask_fn=_fake), ensure_ascii=False, indent=2))
    print(json.dumps(understand("این فایل رو حذف کن", ask_fn=_fake), ensure_ascii=False, indent=2))
