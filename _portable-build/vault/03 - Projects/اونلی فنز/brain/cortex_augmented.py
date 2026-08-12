#!/usr/bin/env python3
"""cortex_augmented.py — مغزِ پوششیِ غنی‌شده با cortex مرکزی (۲۰۲۶-۰۷-۲۵).

زمینه: DualBrainV3 (brain/dual_brain_v3.py) کاملاً rule-based است — ۱۰ ThinkingAgent
همگی با درصدهای هاردکد و lookup-table کار می‌کنند، صفر LLM. این برای shadow-mode
و $0-آفلاین عالی است، ولی «هوشمندی» واقعی ندارد.

این ماژول یک facade می‌سازد: CortexAugmentedBrain، که DualBrainV3 را unchanged
می‌گذارد و فقط وقتی flag روشن است، یک insight استراتژیکِ عمیق از cortexِ مرکزی
به thoughts اضافه می‌کند (نه جایگزینی). وقتی flag خاموش است، رفتار byte-for-byte
با DualBrainV3 است.

مرزِ سختِ #۷ (قفل‌شده): promptی که به cortex می‌رود فقط اعداد abstract دارد
(visitors/subscribers/ppv_buyers/season/drafts_count). هرگز:
  • نام پارتنر/مالک/شهر (PII)
  • محتوای برند/caption/hook
  • نام پلتفرم (OF/Reddit/X)
  • هرچه identity-revealing باشد

این مرز برای حفظِ containment لازم است: cortex اختاپوس یک ارگانیسمِ مشترکه و
نباید بداند این تحلیل دربارهٔ کی یا چه برندی است. فقط اعدادِ یک «سناریوی
بازاریابیِ انتزاعی» می‌بیند.

طراحی:
  • CortexAugmentedBrain(thinking=...) — فیلدِ thinking یک DualBrainV3 واقعی است.
  • think_and_communicate() — امضای هم‌ارز DualBrainV3. اول DualBrainV3 را صدا
    می‌زند، بعد (اگه flag روشن) یک cortex insight اضافه می‌کند.
  • flag: OCTOPUS_WIRE_PROJECTF_CORTEX (همان cortex_client). افزودنی، fail-soft.

$0 · fail-soft · additive.
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PROJ = _HERE.parent
if str(_PROJ) not in sys.path:
    sys.path.insert(0, str(_PROJ))


class CortexAugmentedBrain:
    """مغزِ پوششی: DualBrainV3 + (اختیاری) insight از cortex.

    thinking: یک DualBrainV3 واقعی (تزریق‌شده برای تست). اگر None، یک نمونهٔ
    جدید ساخته می‌شود (lazy import برای جلوگیری از circular).
    """

    CORTEX_TASK = "marketing.strategy"   # نامِ task در cortex (abstract، no PII)
    MAX_TOKENS = 200                      # insight کوتاه — هزینهٔ کم

    def __init__(self, thinking=None):
        if thinking is None:
            # dual_brain_v3 به‌صورتِ flat import می‌شود (هم‌الگوی orchestrator.py:17).
            # اگر brain/ در sys.path باشد، `from dual_brain_v3 import` کار می‌کند؛
            # اگر پروژه به‌صورتِ package import شود، `from brain.dual_brain_v3`.
            # هر دو حالت را امتحان کن (fail-soft).
            try:
                from dual_brain_v3 import DualBrainV3
            except ImportError:
                from brain.dual_brain_v3 import DualBrainV3
            thinking = DualBrainV3()
        self.thinking = thinking

    # ── مرزِ #۷: ساختِ prompt فقط از اعداد (هیچ محتوا) ────────────────────
    @staticmethod
    def _abstract_prompt(visitors: int, subscribers: int, ppv_buyers: int,
                         season: str, drafts_count: int,
                         partner_stress: float) -> str:
        """promptی که فقط اعداد دارد. هرگز PII/محتوا/پلتفرم.

        cortex یک «سناریوی بازاریابیِ انتزاعی» می‌بیند: چند بازدید، چند تبدیل،
        فصل. هیچ اشاره‌ای به صنعت/برند/شخص نیست. این containmentِ سخت است."""
        conv_rate = round(subscribers / max(visitors, 1) * 100, 1)
        ppv_rate = round(ppv_buyers / max(subscribers, 1) * 100, 1)
        return (
            f"Abstract marketing scenario. Visitors={visitors}, "
            f"subscribers={subscribers} ({conv_rate}% conv), "
            f"buyers={ppv_buyers} ({ppv_rate}% of subs), "
            f"season={season}, drafts_in_queue={drafts_count}, "
            f"partner_capacity={partner_stress:.1f}/1.0. "
            f"Give ONE short strategic insight (under 40 words) on the "
            f"single highest-leverage next action. No names, no platform, no niche."
        )

    def think_and_communicate(self, draft_title: str = "",
                              checks: dict | None = None,
                              competitor_data: list[dict] | None = None,
                              post_history: list[dict] | None = None,
                              visitors: int = 100, subscribers: int = 5,
                              ppv_buyers: int = 1, partner_stress: float = 0.3,
                              season: str = "summer",
                              drafts_count: int = 0) -> dict:
        """دورِ کامل: DualBrainV3 + (اختیاری) cortex insight.

        flag خاموش → دقیقاً DualBrainV3 (byte-for-byte).
        flag روشن → DualBrainV3 + یک thoughtِ اضافی با kind='cortex_insight'."""
        # ۱) پایه: DualBrainV3 واقعی (بدون تغییر)
        base = self.thinking.think_and_communicate(
            draft_title=draft_title, checks=checks,
            competitor_data=competitor_data, post_history=post_history,
            visitors=visitors, subscribers=subscribers, ppv_buyers=ppv_buyers,
            partner_stress=partner_stress, season=season,
            drafts_count=drafts_count)
        if base.get("blocked"):
            return base   # compliance بلاک کرده → cortex هم صدا نمی‌زنیم

        # ۲) cortex insight (فقط اگر flag روشن + cortex قابل‌دسترس)
        insight = self._cortex_insight(visitors, subscribers, ppv_buyers,
                                       season, drafts_count, partner_stress)
        if insight:
            base["thoughts"].insert(0, {
                "kind": "cortex_insight",
                "data": {"insight": insight["text"], "tier": insight["tier"],
                         "source": insight["source"], "ms": insight["ms"]},
                "blocked": False,
            })
            # یک پیام هم به messages اضافه کن (مثلِ trend_note)
            base["messages"].append({
                "kind": "cortex",
                "text": f"🧠 insight ({insight['tier']}): {insight['text']}",
                "tone": "advisory",
            })
        return base

    def _cortex_insight(self, visitors, subscribers, ppv_buyers,
                        season, drafts_count, partner_stress) -> dict | None:
        """فراخوانیِ cortex با promptِ abstract. fail-soft → None."""
        try:
            from pf_os import cortex_client
            prompt = self._abstract_prompt(visitors, subscribers, ppv_buyers,
                                           season, drafts_count, partner_stress)
            out = cortex_client.ask(self.CORTEX_TASK, prompt,
                                    max_tokens=self.MAX_TOKENS)
            if out.get("ok") and out.get("text", "").strip():
                return {"text": out["text"].strip()[:300],
                        "tier": out.get("tier", "?"),
                        "source": out.get("source", "cortex"),
                        "ms": out.get("ms", 0)}
            # fallback (flag-off / cortex down) → None، نه دروغ
            return None
        except Exception:  # noqa: BLE001 — fail-soft، هرگز حلقه را نکش
            return None
