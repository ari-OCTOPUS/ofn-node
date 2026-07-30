#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""honest_metric.py — §۰ اکتاپوس‌OS به‌شکلِ کدِ اجراشدنی.

قانونِ بنیادین:
    هر سنجه‌ای که وجودِ خودش را می‌سنجد دروغ می‌گوید — و چون سبز است، کسی شک نمی‌کند.

این ماژول آن قانون را **اجرا‌پذیر** می‌کند. هیچ عددی نمی‌تواند روی تصمیم اثر بگذارد
مگر سه چیز داشته باشد:

    ۱. رسید   (receipt)      — امروز با چه چیزی اندازه گرفته شد
    ۲. برون‌زایی (provenance) — اگر ارگانیسم خاموش شود هم وجود دارد؟
    ۳. وزنِ کیفیت (w_q)      — ضربی، در [0,1]

هفت خرابیِ ۲۵ جولای همه یک بیماری بودند. این ماژول واکسنِ آن بیماری است:

    velocity          → ۹۶.۴٪ متروَنومِ خودش      → self_reference_guard
    moved             → شمارندهٔ کشف‌های خودش      → Provenance.ENDOGENOUS
    innervation 100%  → تازگیِ mtime فایل          → receipt اجباری
    self_awareness    → پوششِ docstring            → receipt اجباری
    germline_alert ok → fallbackی که خرابی بود     → Provenance.ENDOGENOUS
    PLV 0.907         → هم‌فرکانسی، نه اتصال       → w_q + null test
    delta_self 0.0    → منفیِ گردشده               → publish_signed

stdlib-only. صفر وابستگی. fail-closed: نبودِ اطلاعات ⇒ w_q=0، نه پیش‌فرضِ خوش‌بینانه.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "Provenance", "Measurement", "self_reference_share",
    "combine_quality", "publish_signed", "MetricRegistry",
    "SELF_REFERENCE_LIMIT",
]

# اگر بیش از این کسر از یک سنجه از فعالیتِ خودِ ارگانیسم بیاید، خودارجاع است.
SELF_REFERENCE_LIMIT = 0.90
# زیرِ این وزن، سنجه حق رأی ندارد (فقط لاگ می‌شود).
VOTE_THRESHOLD = 0.50


class Provenance(Enum):
    """آیا این عدد بدونِ ارگانیسم هم وجود دارد؟"""

    EXOGENOUS = "exogenous"
    """اگر ارگانیسم خاموش شود هم هست: پولِ تأییدشده، رأیِ انسان، حسگرِ کالیبره."""

    ENDOGENOUS = "endogenous"
    """ارگانیسم خودش تولیدش کرده: شمارندهٔ ضربان، تعدادِ کشف، mtimeِ فایل."""

    DERIVED = "derived"
    """تابعِ چند سنجهٔ دیگر — ضعیف‌ترین والد را به ارث می‌برد."""

    UNKNOWN = "unknown"
    """منشأ نامعلوم. با EXOGENOUS اشتباه نشود — این fail-closed است."""


@dataclass(frozen=True)
class Measurement:
    """یک عددِ صادق: مقدار + منشأ + رسید + وزنِ کیفیت."""

    name: str
    value: float | None
    provenance: Provenance
    receipt: str | None = None
    """چطور امروز اندازه گرفته شد. None ⇒ [UNMEASURABLE YET] ⇒ w_q=0."""
    quality: float = 1.0
    """وزنِ خامِ کیفیت قبل از اعمالِ قواعد."""
    reasons: tuple[str, ...] = ()
    components: dict[str, float] = field(default_factory=dict)
    """اجزای سازندهٔ عدد — برای سنجشِ خودارجاعی."""

    # ---------- قواعدِ اجباری ----------
    @property
    def w_q(self) -> float:
        """وزنِ نهایی. هر تخطی از قواعد آن را به صفر می‌کشد."""
        if self.value is None:
            return 0.0
        if self.receipt is None:                       # قاعدهٔ ۱
            return 0.0
        if self.provenance in (Provenance.ENDOGENOUS, Provenance.UNKNOWN):
            return 0.0                                  # قاعدهٔ ۲ — حق رأی ندارد
        q = max(0.0, min(1.0, float(self.quality)))
        if self.components:                             # قاعدهٔ ۳
            share = self_reference_share(self.components)
            if share > SELF_REFERENCE_LIMIT:
                return 0.0
            q *= (1.0 - share)
        return q

    @property
    def may_vote(self) -> bool:
        """آیا این عدد حق دارد روی یک تصمیم اثر بگذارد؟"""
        return self.w_q >= VOTE_THRESHOLD

    @property
    def all_reasons(self) -> tuple[str, ...]:
        out = list(self.reasons)
        if self.value is None:
            out.append("[UNMEASURABLE YET] مقدار وجود ندارد")
        if self.receipt is None:
            out.append("[UNMEASURABLE YET] رسید ندارد — امروز با چه چیزی سنجیده شد؟")
        if self.provenance is Provenance.ENDOGENOUS:
            out.append("درون‌زاد — ارگانیسم خودش تولیدش کرده؛ لاگ بله، رأی نه")
        if self.provenance is Provenance.UNKNOWN:
            out.append("منشأ نامعلوم — fail-closed")
        if self.components:
            s = self_reference_share(self.components)
            if s > SELF_REFERENCE_LIMIT:
                out.append(f"خودارجاع: {s:.1%} از خودِ ارگانیسم می‌آید (سقف {SELF_REFERENCE_LIMIT:.0%})")
        return tuple(out)

    def as_dict(self) -> dict:
        return {
            "name": self.name, "value": self.value,
            "provenance": self.provenance.value, "receipt": self.receipt,
            "w_q": round(self.w_q, 4), "may_vote": self.may_vote,
            "self_reference_share": (round(self_reference_share(self.components), 4)
                                     if self.components else None),
            "reasons": list(self.all_reasons),
        }


# ---------------------------------------------------------------- توابعِ کمکی
def self_reference_share(components: dict[str, float]) -> float:
    """کسری از یک سنجه که از فعالیتِ خودِ ارگانیسم می‌آید.

    کلیدهایی که با `_self` تمام می‌شوند درون‌زاد شمرده می‌شوند.
    نمونهٔ واقعی (۲۵ جولای): velocity با components
        {"beats_self": 1356, "confirmed": 0, "effects": 0, "consolidation_self": 5}
    ⇒ share = 1361/1361 = 1.0 ⇒ w_q = 0
    """
    total = sum(abs(float(v)) for v in components.values())
    if total <= 0:
        return 0.0
    own = sum(abs(float(v)) for k, v in components.items() if k.endswith("_self"))
    return own / total


def combine_quality(*weights: float) -> float:
    """ترکیبِ **ضربی** — ضعفِ هر مؤلفه کلِ وزن را می‌کشد.

    عمداً ضربی است نه میانگین: میانگین اجازه می‌دهد یک مؤلفهٔ صفر با بقیه جبران شود،
    و همین‌طوری است که «۱۰۰٪ عصب‌دار» کنارِ «۰ لِگِ زنده» می‌نشیند.
    """
    q = 1.0
    for w in weights:
        q *= max(0.0, min(1.0, float(w)))
    return q


def publish_signed(raw: float, floor: float | None = None) -> float:
    """عددِ منفی را منتشر کن. clamp ممنوع.

    ۲۵ جولای: delta_self_raw = -0.02573 ولی 0.0 منتشر می‌شد. آن clamp این واقعیت را
    پنهان می‌کرد که مدلِ خودیِ ارگانیسم از کورِ محض بدتر پیش‌بینی می‌کند — که یک
    واقعیتِ قابلِ اقدام است، نه چیزی برای قایم‌کردن.
    """
    v = float(raw)
    if floor is not None and v < floor:
        return float(floor)
    return v


class MetricRegistry:
    """دفترِ سنجه‌ها. فقط سنجه‌های دارای رأی به تصمیم می‌رسند."""

    def __init__(self) -> None:
        self._m: dict[str, Measurement] = {}

    def put(self, m: Measurement) -> Measurement:
        self._m[m.name] = m
        return m

    def get(self, name: str) -> Measurement | None:
        return self._m.get(name)

    def voters(self) -> list[Measurement]:
        return [m for m in self._m.values() if m.may_vote]

    def silenced(self) -> list[Measurement]:
        return [m for m in self._m.values() if not m.may_vote]

    def report(self) -> dict:
        v, s = self.voters(), self.silenced()
        return {
            "schema": "honest-metrics.v1",
            "n_total": len(self._m), "n_voting": len(v), "n_silenced": len(s),
            "voting": [m.as_dict() for m in v],
            "silenced": [m.as_dict() for m in s],
        }

    def weighted(self, name: str, default: float = 0.0) -> float:
        """مقدارِ وزن‌دار — سنجهٔ بی‌رأی صفر می‌شود، نه اینکه بی‌سر و صدا رد شود."""
        m = self._m.get(name)
        if m is None or m.value is None:
            return default
        return float(m.value) * m.w_q
