"""
llm.py - poel be model vaqei (Claude) + halat MOCK.

اگر ANTHROPIC_API_KEY ست باشد، از Claude واقعی استفاده می‌شود.
اگر نباشد، حالت MOCK فعال می‌شود: بدون هزینه، با خروجی ساختگیِ قابل‌پیش‌بینی،
که برای تستِ لایه‌ی کنترل (kill-switch/HITL/budget) کافی است.
چک‌لیست #۱: تعداد توکن مصرفی همیشه برگردانده می‌شود تا cost-accounting ممکن شود.
"""
from __future__ import annotations
import os
from dataclasses import dataclass

import config


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int
    mock: bool


class LLMClient:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        self.mock = not self.api_key
        self._client = None
        if not self.mock:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"اتصال به Anthropic ممکن نشد ({e}) - حالت MOCK فعال شد.")
                self.mock = True

    def complete(self, system: str, prompt: str) -> LLMResult:
        if self.mock:
            return self._mock(system, prompt)
        msg = self._client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS_PER_CALL,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        return LLMResult(
            text=text,
            input_tokens=msg.usage.input_tokens,
            output_tokens=msg.usage.output_tokens,
            mock=False,
        )

    def _mock(self, system: str, prompt: str) -> LLMResult:
        """خروجی ساختگیِ متناسب با نقش. روتینگ فقط بر اساس system (نقش)."""
        if "Researcher" in system:
            text = ("یافته‌های جستجو (MOCK):\n"
                    "۱) منبع الف می‌گوید X.\n۲) منبع ب می‌گوید Y.\n"
                    "۳) منبع ج ادعای Z را دارد که نیازمند راستی‌آزمایی است.")
        elif "Analyst" in system:
            text = ("خلاصه‌ی تحلیلی (MOCK): سه منبع بررسی شد؛ روی X و Y هم‌رأیی هست، "
                    "ادعای Z نیازمند راستی‌آزمایی است.")
        else:
            text = "APPROVE - تصمیم ناظر (MOCK): کیفیت قابل‌قبول است."
        return LLMResult(text=text,
                         input_tokens=len(prompt) // 4 + 20,
                         output_tokens=len(text) // 4 + 10,
                         mock=True)
