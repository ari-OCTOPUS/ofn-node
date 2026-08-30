"""اعضای مدلِ واقعی برای شوراهای سایه (2026-08-16، رأی مالک «وصل اعضای مدل»).

لایهٔ وصل — بستهٔ councils خودش import-پاک می‌ماند (تست منع ابزار/source-ban)؛
opinion_fn از اینجا تزریق می‌شود:

  · مسیر مدل: llm.router خودِ 4d (TCB، بودجه‌کپ خودش) با task="summarize"
    ⇒ طبق TASK_ROUTING به ollama (محلی، $0) می‌رود — doctrine محلی-اول.
  · بودجهٔ اتمی عضو: هر عضو حداکثر max_calls فراخوان در طول عمرش؛ بعدش
    stub صادق (بودجه تمام شد) — نه فراخوانِ بی‌سقف.
  · قرارداد نظر: JSON سخت {opinion, evidence[], confidence, dissent?}؛
    parse ناموفق/خالی/بی‌شواهد ⇒ stub با دلیل — هرگز نظرِ ساختگی مدل‌مانده.
  · شورا همچنان سایه است: صفر ابزار، صفر اثر؛ این فقط «صدا»ی عضو است.

گیت‌های COUNCIL-MESH هنگام این وصل (شواهد 2026-08-16):
  read-before-decision ≥0.95 ✓ (1.0, 30/30 windowed) · readback 1/1 (نازک —
  daemon جمع می‌کند) · policy_bypass=0 ✓ (NO-GO 9/9 + enforce TCB زنده) ·
  execution_without_artifact=0 ✓ (capability_token=None، تست) · token_replay=0
  ✓ (تست PEP سایه) · rollback drill ✓ (T11 + ری‌استارت رسمی 04:23-04:34 با
  تشدید -Force). فعال‌سازیِ هر شورا همچنان ممنوع — فقط deliberation.
"""
from __future__ import annotations

import json
import re

from councils.base import CouncilMember

_STUB = {
    "opinion": "", "evidence": [], "confidence": 0.0, "dissent": None,
    "reproducible": False, "policy_violation": False, "falsifiable": True,
}

_SYSTEM = (
    "تو عضوِ سایهٔ یک شورای تصمیم هستی. فقط بحث و پیشنهاد — هیچ ابزاری نداری. "
    "پاسخ را «فقط» به‌صورت JSON بساز: "
    '{"opinion": "<یک جمله>", "evidence": ["<منبع/دلیل>"], '
    '"confidence": <0..1>, "dissent": "<اختلاف‌نظر یا null>"}'
)


def _extract_json(text: str) -> dict | None:
    m = re.search(r"\{.*\}", str(text or ""), re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except ValueError:
        return None
    if not isinstance(d, dict) or not str(d.get("opinion") or "").strip():
        return None
    return d


def make_llm_member(family: str = "ollama-local", task: str = "summarize",
                    max_calls: int = 1, name: str = "llm-shadow") -> CouncilMember:
    """عضو شورا با صدای مدلِ واقعی (سایه). محلی-اول، $0، بودجهٔ اتمی عضو."""
    budget = {"n": 0}

    def opinion_fn(ctx: dict) -> dict:
        out = dict(_STUB)
        if budget["n"] >= max_calls:
            out["opinion"] = "__member_budget_exhausted__"
            return out
        budget["n"] += 1
        try:
            from llm.router import LLMRouter
            t = ctx.get("task") or {}
            prompt = (f"نوع کار: {t.get('kind', '?')}\n"
                      f"پرسش: {str(t.get('q', ''))[:400]}\n"
                      f"نظرِ تو به‌عنوان عضو شورا (فقط JSON):")
            text = LLMRouter().ask(prompt, system=_SYSTEM, task=task)
            d = _extract_json(text)
            if d is None:
                out["opinion"] = "__member_unparseable__"
                out["dissent"] = f"raw[:80]={str(text)[:80]!r}"
                return out
            out["opinion"] = str(d["opinion"])[:400]
            ev = d.get("evidence")
            out["evidence"] = [str(e)[:120] for e in ev][:4] if isinstance(ev, list) else []
            try:
                c = float(d.get("confidence", 0.0))
            except (TypeError, ValueError):
                c = 0.0
            out["confidence"] = min(1.0, max(0.0, c))
            if d.get("dissent"):
                out["dissent"] = str(d["dissent"])[:300]
        except Exception as e:  # noqa: BLE001 — عضو نمی‌میرد، شورا هم نه
            out["opinion"] = "__member_error__"
            out["dissent"] = f"{type(e).__name__}: {e}"[:200]
        return out

    return CouncilMember(name, family, opinion_fn)


def augment_architecture_council():
    """شورای معماری + یک عضو مدلِ واقعی (سایه) — استاب‌ها می‌مانند."""
    from councils.councils_phase1 import ArchitectureCouncil
    c = ArchitectureCouncil()
    c.members.append(make_llm_member(family="ollama-local"))
    return c
