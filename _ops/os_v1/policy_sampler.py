#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""policy_sampler.py — نمونه‌گیرِ سیاست، با قیدِ سختِ **اثبات‌پذیر**.

## دو کارِ این فایل

**۱ — رابط را باز نگه می‌دارد.** اگر روزی سخت‌افزارِ نمونه‌گیرِ فیزیکی (ترمودینامیکی)
واقعی شد، جایگزینی یک کلاس است، نه بازنویسیِ هستهٔ تصمیم. هزینهٔ این کار **امروز صفر** است.

**۲ — قید را از جریمه جدا می‌کند، در سطحِ ساختارِ داده.**
این تفاوت مسئلهٔ **ایمنی** است، نه بهینه‌سازی:

    جریمه: G[i] += 1e9      ⇒ احتمالِ خیلی کم، ولی **نه صفر**
    قید  : از آرایه حذف     ⇒ احتمالِ **دقیقاً صفر**

در `1e9` جریمه، با `γ` کوچک یا سرریزِ عددی، آن سیاست بالاخره یک بار انتخاب می‌شود.
«یک بار در میلیون» برای کنشِ برگشت‌ناپذیر یعنی «حتماً، فقط دیرتر».

پس قید اینجا **حذف** می‌کند: سیاستِ ممنوع اصلاً واردِ توزیع نمی‌شود.

> نکتهٔ مهم برای ارزیابیِ سخت‌افزارِ آینده (پرامپتِ C5):
> یک نمونه‌گیرِ فیزیکی معمولاً احتمال را **کم** می‌کند، نه صفر. اگر سخت‌افزاری
> نتواند «دقیقاً صفر» را تضمین کند، برای این هسته **قابلِ استفاده نیست** — مگر آنکه
> ماسک بیرون از آن، در دیجیتال، اعمال شود. این معیارِ پذیرشِ ماست.

stdlib-only. بدونِ numpy، تا در همان محیطی اجرا شود که بقیهٔ هسته اجرا می‌شود.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

__all__ = ["Policy", "SamplerResult", "PolicySampler", "CpuSoftmaxSampler",
           "ConstraintViolation"]


class ConstraintViolation(RuntimeError):
    """نمونه‌گیر سیاستِ ممنوع برگرداند. این هرگز نباید رخ دهد."""


@dataclass(frozen=True)
class Policy:
    name: str
    G: float                      # انرژیِ آزادِ منتظره — کمتر بهتر
    allowed: bool = True          # قید: نه جریمه، حذف
    reason: str = ""              # اگر ممنوع است، چرا


@dataclass(frozen=True)
class SamplerResult:
    names: list[str]
    probs: list[float]
    removed: list[str]
    gamma: float
    backend: str

    @property
    def best(self) -> str | None:
        return max(zip(self.names, self.probs), key=lambda t: t[1])[0] if self.names else None

    def p(self, name: str) -> float:
        """احتمالِ یک سیاست. سیاستِ حذف‌شده **دقیقاً** صفر است."""
        for n, q in zip(self.names, self.probs):
            if n == name:
                return q
        return 0.0

    def as_dict(self) -> dict:
        return {"schema": "policy-sample.v1", "backend": self.backend,
                "gamma": self.gamma, "removed": self.removed,
                "dist": dict(zip(self.names, [round(p, 6) for p in self.probs]))}


class PolicySampler:
    """رابط. هر backendِ آینده — از جمله سخت‌افزارِ فیزیکی — این را پیاده می‌کند."""

    backend = "abstract"

    def distribution(self, policies: list[Policy], gamma: float) -> SamplerResult:
        raise NotImplementedError

    # ------------------------------------------------------------------ گارد
    @staticmethod
    def _mask(policies: list[Policy]) -> tuple[list[Policy], list[str]]:
        """قید **قبل از** هر محاسبه‌ای اعمال می‌شود. حذف، نه وزنِ کم."""
        keep = [p for p in policies if p.allowed]
        drop = [f"{p.name} ({p.reason or 'قید'})" for p in policies if not p.allowed]
        return keep, drop

    def sample(self, policies: list[Policy], gamma: float = 4.0,
               rng: random.Random | None = None) -> str | None:
        """یک انتخاب. اگر سیاستِ ممنوع برگردد، **استثنا** — نه لاگ."""
        res = self.distribution(policies, gamma)
        if not res.names:
            return None
        r = (rng or random).random()
        acc = 0.0
        pick = res.names[-1]
        for n, q in zip(res.names, res.probs):
            acc += q
            if r <= acc:
                pick = n
                break
        banned = {p.name for p in policies if not p.allowed}
        if pick in banned:                                      # گاردِ کمربند-و-بند
            raise ConstraintViolation(f"⛔ سیاستِ ممنوع انتخاب شد: {pick}")
        return pick


class CpuSoftmaxSampler(PolicySampler):
    """پیاده‌سازیِ مرجع: softmax روی CPU با ماسکِ قطعی.

    پایدارِ عددی (کم‌کردنِ کمینه پیش از exp) تا با `γ` بزرگ سرریز نکند —
    سرریز راهِ دیگری است که «احتمالِ صفر» بی‌سروصدا به NaN تبدیل می‌شود.
    """

    backend = "cpu-softmax"

    def distribution(self, policies: list[Policy], gamma: float = 4.0) -> SamplerResult:
        keep, drop = self._mask(policies)
        if not keep:
            return SamplerResult([], [], drop, gamma, self.backend)
        g = max(0.0, float(gamma))
        gmin = min(p.G for p in keep)
        raw = [math.exp(-g * (p.G - gmin)) for p in keep]
        s = sum(raw)
        if s <= 0 or not math.isfinite(s):                       # γ عظیم ⇒ عملاً argmin
            probs = [1.0 if p.G == gmin else 0.0 for p in keep]
            s = sum(probs) or 1.0
            probs = [x / s for x in probs]
        else:
            probs = [x / s for x in raw]
        return SamplerResult([p.name for p in keep], probs, drop, g, self.backend)
