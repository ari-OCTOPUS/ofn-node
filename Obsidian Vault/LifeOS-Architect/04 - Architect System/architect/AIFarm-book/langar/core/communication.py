"""
communication.py — مدیریتِ لحن، طول و زمانِ ارتباط.

خالص است. فقط فرمِ پیام را تنظیم می‌کند، نه محتوای منطقیِ سؤال را.
خروجی همچنان از gate در bot عبور می‌کند (این لایه gate را دور نمی‌زند).
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass

_EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF←-⇿⬀-⯿]"
)


@dataclass
class CommunicationStyle:
    tone: str = "direct"          # direct | warm | minimal | probing
    max_length: int = 3           # حداکثر «خط»های محتوایی
    timing_sensitivity: float = 0.3
    emoji_usage: bool = True


class CommunicationManager:
    def decide_style(self, mm: dict | None, context: dict | None = None) -> CommunicationStyle:
        mm = mm or {}
        ctx = context or {}
        hour = ctx.get("hour", _dt.datetime.now().hour)
        stress = float(mm.get("stress_level", 0.5))
        engagement = float(mm.get("engagement", 0.5))
        rmssd_low = bool(ctx.get("rmssd_low", False))
        night = hour < 7 or hour >= 23

        if stress > 0.7 or night:
            tone = "minimal"
        elif rmssd_low:
            tone = "probing"
        else:
            tone = mm.get("preferred_tone", "direct")

        max_length = 2 if (stress > 0.7 or night or engagement < 0.35) else 3
        timing = 0.8 if (night or stress > 0.7) else 0.3
        return CommunicationStyle(tone=tone, max_length=max_length,
                                  timing_sensitivity=timing,
                                  emoji_usage=(tone != "minimal"))

    def adapt_message(self, raw: str, style: CommunicationStyle) -> str:
        """فرمِ پیام را تنظیم می‌کند؛ محتوای سؤال (خطِ ❓) همیشه حفظ می‌شود."""
        lines = [ln for ln in raw.split("\n") if ln.strip()]
        if style.tone == "minimal":
            # فقط خطِ سؤال را نگه دار
            q = next((ln for ln in lines if "❓" in ln), None)
            lines = [q] if q else lines[:1]
        elif len(lines) > style.max_length:
            lines = lines[:style.max_length]
        out = "\n".join(lines)
        if not style.emoji_usage:
            out = _EMOJI.sub("", out).strip()
        return out
