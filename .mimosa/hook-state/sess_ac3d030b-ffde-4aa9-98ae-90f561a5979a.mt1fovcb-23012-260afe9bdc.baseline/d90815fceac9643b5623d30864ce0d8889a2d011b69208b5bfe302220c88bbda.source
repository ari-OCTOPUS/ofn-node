"""constitution.py — ۱۴ قانونِ آهنین (گذرگاهِ critique). خالص، با نرمال‌سازیِ اعراب."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PRINCIPLES = [
    "در شک: سکوت", "RMSSD شاخصِ قفل‌شده است", "verdict برگشت‌ناپذیر است",
    "همبستگی ≠ علیت", "ادعاها تگِ قطعیت بگیرند", "پزشک نیستیم",
    "تقویتِ نشخوارِ منفی ممنوع", "عادی‌سازیِ خودتخریبی ممنوع", "صداقتِ N-of-1",
    "حوزه‌ی مهندسی هفتگی", "خودبهبود شفاف", "تغییرِ خودکار فقط وزن",
    "حفظِ حریمِ خصوصی", "تناسبِ ارتباط",
]

_DIACRITICS = re.compile(r"[ً-ْٰـ]")


def _norm(s: str) -> str:
    s = s.translate({0x064A: 0x06CC, 0x0643: 0x06A9})
    return _DIACRITICS.sub("", s)


_MEDICAL = re.compile(r"(تجویز|تشخیص\s*می|بیماری.{0,12}داری|قرص.{0,8}بخور|دارو.{0,8}بخور|دوز\s*دارو)")
_CAUSAL = re.compile(r"(باعث.{1,30}(شد|می‌شود|شده)|علت.{1,20}(است|بود))")
_HEDGE = re.compile(r"(شاید|ممکن|احتمال|نشانه|همبستگی|به\s*نظر|گویا|علیت نیست)")
_RUMINATION = re.compile(r"(چرا همیشه|چرا هیچ\s*وقت|بدترین\s*آدم|همیشه شکست|هیچ\s*وقت موفق)")
_SELF_HARM_OK = re.compile(r"(اشکالی ندارد.{0,15}(آسیب|زخم|گرسنه)|طبیعی است.{0,15}(نخوری|نخوابی))")


@dataclass
class Critique:
    compliant: bool = True
    violations: list = field(default_factory=list)


def critique(text: str, context: dict | None = None) -> Critique:
    c = Critique()
    if not text or not text.strip():
        c.compliant = False
        c.violations.append("متنِ خالی")
        return c
    t = _norm(text)
    if _MEDICAL.search(t):
        c.violations.append("قانون ۶: ادعای پزشکی")
    if _CAUSAL.search(t) and not _HEDGE.search(t):
        c.violations.append("قانون ۴: ادعای علیت بدونِ احتیاط")
    if _RUMINATION.search(t):
        c.violations.append("قانون ۷: تقویتِ نشخوار")
    if _SELF_HARM_OK.search(t):
        c.violations.append("قانون ۸: عادی‌سازیِ خودتخریبی")
    c.compliant = not c.violations
    return c


def is_compliant(text: str, context: dict | None = None) -> bool:
    return critique(text, context).compliant
