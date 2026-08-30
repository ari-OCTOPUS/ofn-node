"""گاردِ ظرفیت (قیدِ مقدمِ D4) — تابعِ خالص، بدونِ I/O، کاملاً تست‌پذیر.

قاعدهٔ منشورِ زیمان (PROJECT.md):
  «هیچ draft کمپینی که تقاضای بالاتر از سقفِ ظرفیت بسازد تولید نمی‌شود —
   ایجنت باید رد کند و دلیل بیاورد.»
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CapacityVerdict:
    approved: bool
    ceiling: int
    horizon_weeks: int
    max_allowed: int
    requested: int
    reason: str


def check_campaign(requested_units: int, ceiling: int, horizon_weeks: int = 1) -> CapacityVerdict:
    """آیا کمپینی با هدفِ requested_units واحد در بازهٔ horizon_weeks مجاز است؟"""
    requested_units = int(requested_units)
    ceiling = int(ceiling)
    if ceiling <= 0:
        return CapacityVerdict(False, ceiling, horizon_weeks, 0, requested_units,
                               "سقفِ ظرفیت ثبت نشده یا صفر است — تا ثبتِ عدد، هیچ کمپینی مجاز نیست (اول ظرفیت).")
    if horizon_weeks < 1:
        horizon_weeks = 1
    max_allowed = ceiling * horizon_weeks
    if requested_units <= 0:
        return CapacityVerdict(True, ceiling, horizon_weeks, max_allowed, requested_units,
                               "بدونِ هدفِ حجمی (محتوای معمولی) — مجاز.")
    if requested_units > max_allowed:
        return CapacityVerdict(
            False, ceiling, horizon_weeks, max_allowed, requested_units,
            f"رد شد (D4): هدفِ {requested_units} واحد از سقفِ {max_allowed} واحد "
            f"({ceiling}/هفته × {horizon_weeks} هفته) بیشتر است. "
            f"«اول ظرفیت، بعد کمپین» — یا هدف را به ≤{max_allowed} کم کن یا سقفِ ظرفیت را بالا ببر.")
    return CapacityVerdict(True, ceiling, horizon_weeks, max_allowed, requested_units,
                           f"تأیید شد: {requested_units} ≤ {max_allowed} واحد در {horizon_weeks} هفته.")
