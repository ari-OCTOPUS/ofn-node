# -*- coding: utf-8 -*-
"""پلِ LLM → Observation. مدل‌ها مشاورند، نه مرجع.

مسیرِ پیش‌فرض (lazy، fail-soft): cortex.model_router.ask (درِ واحدِ ارگانیسم؛
خودش محلی-اول/Qwen→Fugu را مدیریت می‌کند) → local_llm.ask → None.
- خروجی باید JSONِ سخت‌گیر مطابقِ schema باشد؛ JSONِ خراب = (None, reason) — هرگز حدس.
- evidence_strength خروجیِ LLM سقفِ 0.5 دارد: «حرفِ مدل» هرگز هم‌وزنِ تست نیست.
- هیچ secret/prompt-injection ای وارد نمی‌شود: خلاصه scrub می‌شود.
"""
from __future__ import annotations

import json
import re

from ..observation import scrub_summary
from ..schemas import Observation, clamp01

LLM_STRENGTH_CAP = 0.5
_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)

SCHEMA_PROMPT = """You convert one raw observation text into strict JSON. Output ONLY JSON, no prose.
Schema:
{
  "payload_summary": "<short factual summary, no secrets, max 300 chars>",
  "evidence_strength": <float 0..1, how directly the text evidences a system fact>,
  "dim_claims": {"<dimension>": <float 0..1>, ...}   // only dimensions you can justify
}
Allowed dimensions: evidence_quality, test_health, goal_alignment, operational_risk,
reversibility, cost_budget, uncertainty, dependency_health.
If the text is ambiguous or you cannot justify a claim, return {"payload_summary": "...",
"evidence_strength": 0.1, "dim_claims": {}} — never invent."""


def _default_ask(prompt: str) -> str | None:
    """درِ واحدِ ارگانیسم؛ در سندباکس/آفلاین بی‌صدا None (تست‌ها ask_fn تزریق می‌کنند)."""
    try:
        from cortex import model_router  # lazy — فقط وقتی واقعاً داخلِ ارگانیسم هستیم
        r = model_router.ask("chord.extract", prompt, system=SCHEMA_PROMPT,
                             max_tokens=300)
        if isinstance(r, dict) and r.get("ok") and r.get("text"):
            return str(r["text"])
    except Exception:  # noqa: BLE001
        pass
    try:
        from cortex import local_llm
        r = local_llm.ask(prompt, system=SCHEMA_PROMPT, max_tokens=300)
        if isinstance(r, dict) and r.get("text"):
            return str(r["text"])
    except Exception:  # noqa: BLE001
        pass
    return None


def extract_observation(raw_text: str, source_ref: str,
                        mission_id: str = "",
                        ask_fn=None) -> tuple:
    """(Observation|None, dim_claims: dict, reason: str).
    ask_fn(prompt)->str|None قابلِ‌تزریق برای تست/روترِ دلخواه."""
    raw_text = (raw_text or "").strip()
    if not raw_text:
        return None, {}, "empty-input"
    if not (source_ref or "").strip():
        return None, {}, "missing-source_ref (provenance is mandatory)"

    ask = ask_fn or _default_ask
    try:
        out = ask(f"OBSERVATION TEXT:\n{scrub_summary(raw_text)}\nJSON:")
    except Exception as e:  # noqa: BLE001 — مشاورِ خراب نباید هسته را بکشد
        return None, {}, f"llm-error:{type(e).__name__}"
    if not out:
        return None, {}, "llm-unavailable (offline is a valid state → UNKNOWN upstream)"

    m = _JSON_BLOCK.search(str(out))
    if not m:
        return None, {}, "malformed-llm-output:no-json"
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, {}, "malformed-llm-output:bad-json"
    if not isinstance(data, dict) or "payload_summary" not in data:
        return None, {}, "malformed-llm-output:missing-keys"

    claims_in = data.get("dim_claims") or {}
    if not isinstance(claims_in, dict):
        return None, {}, "malformed-llm-output:dim_claims-not-dict"
    from ..schemas import DIMENSIONS
    dim_claims = {d: clamp01(v) for d, v in claims_in.items() if d in DIMENSIONS}

    ob = Observation(
        source_type="llm", source_ref=source_ref,
        payload_summary=scrub_summary(str(data.get("payload_summary", ""))),
        evidence_strength=min(LLM_STRENGTH_CAP,
                              clamp01(data.get("evidence_strength", 0.1), 0.1)),
        mission_id=mission_id, provenance="llm-adapter(model_router|local)",
    )
    errs = ob.validate()
    if errs:
        return None, {}, "invalid-observation:" + ";".join(errs)
    return ob, dim_claims, "ok"
