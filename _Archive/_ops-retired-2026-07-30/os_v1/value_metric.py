#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""value_metric.py — «ارزش بر وات» بدونِ خطای واحد.

## چرا این فایل وجود دارد

در طرحِ اولیه نوشته بودم:

    value_per_dollar = نتیجهٔ برون‌زاد / (دلارِ خرج‌شده + وات‌ساعتِ مصرف‌شده)

**این غلط است.** دلار و وات‌ساعت دو واحدِ متفاوت‌اند؛ جمعشان بی‌معناست. عددی که از آن
درمی‌آید ظاهرِ سالمی دارد، بالا و پایین می‌رود، و کسی شکش نمی‌کند — یعنی **دقیقاً همان
بیماریِ §۰**، این بار در قالبِ تحلیلِ ابعادی.

پس این ماژول جمع‌کردنشان را **ساختاراً ناممکن** می‌کند، نه اینکه در مستندات هشدار بدهد.

    Quantity(3.0, "usd") + Quantity(1.0, "wh")   ⇒  UnitError

دو سنجه، جدا، هرکدام با واحدِ خودش:
    value_per_usd  — واحد: نتیجه بر دلار
    value_per_wh   — واحد: نتیجه بر وات‌ساعت

stdlib-only.
"""
from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Quantity", "UnitError", "Ratio", "value_per_usd", "value_per_wh",
           "efficiency_report", "USD", "WH", "OUTCOME"]

USD = "usd"
WH = "wh"
OUTCOME = "outcome"          # نتیجهٔ برون‌زادِ تأییدشده — بی‌بعد، شمارشی


class UnitError(TypeError):
    """جمع یا مقایسهٔ دو واحدِ ناهمگن. عمداً استثناست، نه هشدار."""


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str

    def __post_init__(self) -> None:
        if not self.unit:
            raise UnitError("کمیتِ بی‌واحد وجود ندارد")
        if self.value < 0:
            # عددِ منفی clamp نمی‌شود (R-02) ولی هزینهٔ منفی معنا ندارد
            object.__setattr__(self, "value", float(self.value))

    def __add__(self, other: "Quantity") -> "Quantity":
        if not isinstance(other, Quantity):
            raise UnitError(f"جمعِ Quantity با {type(other).__name__}")
        if other.unit != self.unit:
            raise UnitError(
                f"⛔ جمعِ «{self.unit}» با «{other.unit}» بی‌معناست — "
                "دو سنجهٔ جدا بساز، یکی نکن")
        return Quantity(self.value + other.value, self.unit)

    __radd__ = __add__

    def __truediv__(self, other: "Quantity") -> "Ratio":
        if not isinstance(other, Quantity):
            raise UnitError("تقسیم فقط بر Quantity")
        if other.value == 0:
            raise ZeroDivisionError(f"مخرجِ صفر در {self.unit}/{other.unit}")
        return Ratio(self.value / other.value, self.unit, other.unit)


@dataclass(frozen=True)
class Ratio:
    """نسبتِ دو کمیت، با هر دو واحد چسبیده به آن."""
    value: float
    numerator_unit: str
    denominator_unit: str

    @property
    def unit(self) -> str:
        return f"{self.numerator_unit}/{self.denominator_unit}"

    def __add__(self, other):                                   # noqa: ANN001
        raise UnitError(
            "⛔ دو نسبت با هم جمع نمی‌شوند — این همان اشتباهی است که "
            "value_per_dollar را بی‌معنا کرده بود")

    def as_dict(self) -> dict:
        return {"value": round(self.value, 6), "unit": self.unit}

    def __str__(self) -> str:
        return f"{self.value:.4g} {self.unit}"


def value_per_usd(outcomes: float, usd: float) -> Ratio | None:
    """نتیجهٔ برون‌زادِ تأییدشده بر دلارِ خرج‌شده. `None` = هنوز داده نیست."""
    if usd <= 0:
        return None
    return Quantity(outcomes, OUTCOME) / Quantity(usd, USD)


def value_per_wh(outcomes: float, wh: float) -> Ratio | None:
    """نتیجهٔ برون‌زادِ تأییدشده بر وات‌ساعتِ مصرف‌شده."""
    if wh <= 0:
        return None
    return Quantity(outcomes, OUTCOME) / Quantity(wh, WH)


def efficiency_report(outcomes: float, usd: float, wh: float | None) -> dict:
    """گزارشِ دو سنجه، هرگز یکی‌شده.

    `wh=None` یعنی مصرفِ برق هنوز اندازه‌گیری نشده — و `[UNKNOWN]` می‌ماند،
    نه اینکه صفر یا حدسی جایش بنشیند.
    """
    a = value_per_usd(outcomes, usd)
    b = value_per_wh(outcomes, wh) if wh is not None else None
    return {
        "schema": "efficiency.v1",
        "outcomes_exogenous": outcomes,
        "value_per_usd": a.as_dict() if a else None,
        "value_per_wh": b.as_dict() if b else None,
        "unknown": ([] if wh is not None else
                    ["مصرفِ برقِ لپ‌تاپ اندازه‌گیری نشده — value_per_wh نامعلوم"])
                   + ([] if usd > 0 else ["هنوز دلاری خرج نشده"]),
        "note": "این دو هرگز با هم جمع نمی‌شوند. واحدشان متفاوت است.",
    }
