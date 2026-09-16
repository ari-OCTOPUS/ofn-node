"""ziman.py — پای زیمان (هدیه/تجارت؛ کنترل‌برین ۷۶ تست).

روی برد OFN اجرا می‌شود (رأی NBB-V5)؛ این کلاس فقط پروکسیِ لینک است.
رفتار خاص: قالب‌بندی کارت‌های محصول برای مسیر خروجی.
"""
from __future__ import annotations

from nbb_cp.adapters.legs.base import LegAdapter


class ZimanLeg(LegAdapter):
    leg_id = "ziman"
    budget_cap_aud = 20.0

    CARD_PREFIX = "🌸"

    def transform_outbound(self, text: str) -> str:
        """کارت زیمان: پیشوند گل + جمع‌کردن فاصله‌ها (نمونهٔ رفتار خاص per-leg)."""
        compact = " ".join(str(text or "").split())
        return f"{self.CARD_PREFIX} {compact}" if compact else ""
