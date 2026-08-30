"""compose.py — Response Composer / Disclosure Guard (بازبینیِ Hypothesis-Ledger).

پاسخ را در دو کانالِ مجزا می‌سازد تا مدل هرگز یک belief ledger را به‌صورت fact
خارجی render نکند:

  Observed facts   — فقط evidence verified یا runtime_truth (world_mode=reality)
  Hypotheses       — claim با confidence/evidencecounter/prediction/disclosure
                     (world_mode ≠ reality)

این تنها زمانی به چت می‌رسد که epistemic واقعاً وصل شود (post-Go). فعلاً یک
ماژولِ pure است که Hub/صفتِ نمایش می‌توانند از آن استفاده کنند.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class ComposedResponse:
    """خروجیِ دو-کاناله."""
    observed_facts: List[str] = field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)
    disclosure: str = ""        # unverified/simulation/counterfactual
    has_leakage: bool = False   # اگر claimی با world_mode≠reality در facts رفته باشد


def compose(*, observed: List[str] = None, claims: List[Dict[str, Any]] = None,
            runtime_truth: str = "") -> ComposedResponse:
    """دو کانال بساز و label-leakage را بگیر.

    claims: هرکدام dict با world_mode/epistemic_status/confidence/prediction/falsifier.
    observed: فکت‌های verified. runtime_truth: متنِ runtime (همیشه reality)."""
    observed = list(observed or [])
    claims = list(claims or [])
    facts = list(observed)
    if runtime_truth:
        facts.append(runtime_truth)

    hyps: List[Dict[str, Any]] = []
    leakage = False
    for c in claims:
        wm = str(c.get("world_mode") or "hypothesis")
        if wm == "reality":
            # invariant #4: یک claimِ epistemic نباید reality باشد — اگر بود، leakage.
            leakage = True
            continue
        hyps.append({
            "id": c.get("claim_id") or c.get("id"),
            "world_mode": wm,
            "epistemic_status": c.get("epistemic_status", "unverified"),
            "confidence": c.get("confidence"),
            "prediction": c.get("prediction") or c.get("predictions"),
            "falsifier": c.get("falsifier"),
            "disclosure": _disclosure(wm, c.get("epistemic_status")),
        })

    # disclosure کلی: قوی‌ترینِ غیرِواقعیت
    modes = {h["world_mode"] for h in hyps}
    if "counterfactual" in modes:
        disc = "counterfactual"
    elif "simulation" in modes:
        disc = "simulation"
    elif "fictional" in modes:
        disc = "fictional"
    elif modes:
        disc = "unverified"
    else:
        disc = ""

    return ComposedResponse(observed_facts=facts, hypotheses=hyps,
                            disclosure=disc, has_leakage=leakage)


def _disclosure(world_mode: str, epistemic_status: str) -> str:
    if world_mode in ("simulation", "counterfactual", "fictional"):
        return world_mode
    if epistemic_status in ("supported",):
        return "supported-not-proven"
    return "unverified"


def render_text(comp: ComposedResponse) -> str:
    """رندرِ متنِ دو-کاناله برای نمایش."""
    lines = []
    if comp.observed_facts:
        lines.append("Observed facts (verified/runtime):")
        for f in comp.observed_facts:
            lines.append(f"  · {f}")
    if comp.hypotheses:
        lines.append("")
        lines.append("Hypotheses (unverified):")
        for h in comp.hypotheses:
            lines.append(f"  · [{h['disclosure']}] {h.get('prediction') or h.get('id')}"
                         + (f" (confidence={h.get('confidence')})" if h.get('confidence') else ""))
    if comp.has_leakage:
        lines.append("")
        lines.append("🛑 WARNING: یک claim سعی کرد به‌عنوان fact نمایش داده شود — مسدود شد.")
    if comp.disclosure:
        lines.append("")
        lines.append(f"Disclosure: {comp.disclosure}")
    return "\n".join(lines) if lines else "(هیچ فکت/فرضیه‌ای برای نمایش نیست)"
