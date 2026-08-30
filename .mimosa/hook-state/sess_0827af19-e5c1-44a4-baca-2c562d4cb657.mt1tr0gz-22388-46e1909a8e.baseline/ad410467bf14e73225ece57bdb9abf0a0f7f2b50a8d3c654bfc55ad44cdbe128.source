#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""router.py — مسیریابیِ هزینه‌محور: کد ⟶ مدلِ محلی ⟶ ابر.

معادلِ نرم‌افزاریِ کاری که NVIDIA در سخت‌افزار کرد: سیلیکونِ استنتاج را از سیلیکونِ
آموزش جدا کرد. اینجا هم هر پرسش به **ارزان‌ترین لایه‌ای که از پسش برمی‌آید** می‌رود،
نه به بهترین مدلی که در دسترس است.

    L0/L1  کد        — قطعی، صفر دلار، صفر تأخیر. اگر جواب معین است، مدل نمی‌خواهیم.
    L2/L3  محلی      — تریاژ، خلاصه، امضا، «این نویز است؟». صفر دلار.
    L4     ابر       — فقط تشخیصِ عمیق و نوشتنِ پچ. ~$۰٫۲۲ هر بار.

سه قاعده که در کد اجرا می‌شوند:
  ۱ **تشدید فقط رو به بالا، و فقط با دلیل.** هیچ کاری بی‌دلیل به ابر نمی‌رود.
  ۲ **نبودِ مدلِ محلی ⇒ سقوط به کد، نه ترفیع به ابر.** وگرنه هر نصبِ ناقص
    بی‌سروصدا قبضِ ماهانه را ده‌برابر می‌کند.
  ۳ **بودجه بر ترجیح مقدم است.** با سقفِ دلارِ تمام‌شده، ابر بسته است حتی برای
    کارِ پرریسک — و همین صریح گزارش می‌شود.

stdlib-only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import IntEnum

__all__ = ["Tier", "Task", "Decision", "Router"]


class Tier(IntEnum):
    CODE = 0        # بدونِ مدل
    LOCAL = 1       # مدلِ روی لپ‌تاپ
    CLOUD = 2       # fugu — پولی
    NONE = 3        # هیچ‌کس نمی‌تواند؛ به مالک گزارش می‌شود


# کارهایی که جوابشان **معین** است. مدل برایشان اتلاف است، و بدتر: منبعِ توهم.
DETERMINISTIC = {
    "count", "diff", "hash", "parse", "dedupe", "signature",
    "threshold", "schema-validate", "regex", "sort", "sum",
}
# کارهایی که تصمیمِ برگشت‌ناپذیر یا کدِ اجرایی تولید می‌کنند.
HIGH_STAKES = {"propose", "patch", "merge-advice", "security-audit", "root-cause"}

_RISKY = re.compile(r"(حذف|delete|drop|rm\s|فرمت|format|توکن|token|راز|secret|"
                    r"\.env|merge|push|force)", re.IGNORECASE)


@dataclass(frozen=True)
class Task:
    kind: str
    text: str = ""
    risk: str = "low"              # low | medium | high
    needs_code_output: bool = False
    tokens_est: int = 0


@dataclass
class Decision:
    tier: Tier
    reasons: list[str] = field(default_factory=list)
    est_usd: float = 0.0
    degraded: bool = False         # می‌خواستیم بالاتر برویم ولی نشد

    def as_dict(self) -> dict:
        return {"tier": self.tier.name, "est_usd": round(self.est_usd, 4),
                "degraded": self.degraded, "reasons": self.reasons}


class Router:
    def __init__(self, *, local_available: bool = False,
                 cloud_ready: bool = False,
                 usd_remaining: float = 0.0,
                 usd_per_cloud_call: float = 0.22):
        self.local = bool(local_available)
        self.cloud = bool(cloud_ready)
        self.usd_remaining = float(usd_remaining)
        self.usd_per_call = float(usd_per_cloud_call)

    # --------------------------------------------------------------- تصمیم
    def route(self, task: Task) -> Decision:
        d = Decision(Tier.CODE)

        # ۱ — جوابِ معین ⇒ کد. حتی اگر ابر آزاد و ارزان باشد.
        if task.kind in DETERMINISTIC:
            d.reasons.append(f"«{task.kind}» جوابِ معین دارد — مدل اتلاف و منبعِ توهم است")
            return d

        want = Tier.LOCAL
        # ۲ — چه چیزی واقعاً ابر لازم دارد
        if task.kind in HIGH_STAKES:
            want = Tier.CLOUD
            d.reasons.append(f"«{task.kind}» کدِ اجرایی یا تصمیمِ برگشت‌ناپذیر تولید می‌کند")
        elif task.needs_code_output:
            want = Tier.CLOUD
            d.reasons.append("خروجی باید کدِ قابلِ اجرا باشد")
        elif task.risk == "high" or _RISKY.search(task.text or ""):
            want = Tier.CLOUD
            d.reasons.append("متن یا ریسکِ کار پرمخاطره است")
        else:
            d.reasons.append("کارِ کم‌ریسکِ متنی — لایهٔ محلی کافی است")

        # ۳ — بودجه بر ترجیح مقدم است
        if want == Tier.CLOUD:
            if not self.cloud:
                want = Tier.LOCAL
                d.degraded = True
                d.reasons.append("⛔ مغزِ ابری آماده نیست (کلید؟) — تنزل به محلی")
            elif self.usd_remaining < self.usd_per_call:
                want = Tier.LOCAL
                d.degraded = True
                d.reasons.append(
                    f"⛔ سقفِ دلار: باقی‌مانده ${self.usd_remaining:.2f} < "
                    f"${self.usd_per_call:.2f} — تنزل به محلی")
            else:
                d.est_usd = self.usd_per_call

        # ۴ — نبودِ محلی ⇒ سقوط به کد، **نه** ترفیع به ابر
        if want == Tier.LOCAL and not self.local:
            if d.degraded:
                d.tier = Tier.NONE
                d.reasons.append("⛔ نه ابر نه محلی — این کار امروز انجام نمی‌شود")
                return d
            d.tier = Tier.CODE
            d.degraded = True
            d.reasons.append(
                "مدلِ محلی نصب نیست ⇒ سقوط به کد. **به ابر ترفیع نمی‌دهیم** — "
                "وگرنه یک نصبِ ناقص، بی‌سروصدا قبض را ده‌برابر می‌کند")
            return d

        d.tier = want
        return d

    # ------------------------------------------------------------- گزارش
    def plan(self, tasks: list[Task]) -> dict:
        """پیش‌بینیِ هزینهٔ یک روز، قبل از خرج‌شدنش."""
        ds = [self.route(t) for t in tasks]
        by = {t.name: sum(1 for d in ds if d.tier is t) for t in Tier}
        return {"schema": "route-plan.v1", "by_tier": by,
                "est_usd_total": round(sum(d.est_usd for d in ds), 4),
                "degraded": sum(1 for d in ds if d.degraded),
                "blocked": [t.kind for t, d in zip(tasks, ds) if d.tier is Tier.NONE]}
