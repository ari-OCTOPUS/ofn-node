#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""efe.py — انرژیِ آزادِ موردانتظار، در فرمِ **ایمن** (§۳ اکتاپوس‌OS).

## چرا فرمِ سندِ دوپامین رد شد

سندِ آپلودیِ ۲۵ جولای این را پیشنهاد داد:

    G_DA(π) = risk(π) − β_DA · epistemic(π)          ← ❌ ناامن

یعنی β فقط ترمِ epistemic را مقیاس می‌دهد. با β بزرگ، **risk عملاً بی‌اهمیت می‌شود** —
دقیقاً همان «exploitِ خطرناک» که خودِ مالک نگرانش بود.

در فرمول‌بندیِ استانداردِ فریستون، دوپامین **precisionِ باورها دربارهٔ policy** است:

    p(π) ∝ softmax(−γ · G(π))                        ← ✅ γ کلِ G را مقیاس می‌دهد

γ بالا = قاطع‌تر (توزیعِ تیزتر)، نه بی‌پرواتر. این تفاوت، ایمنی است.

## و یک لایهٔ سخت‌تر: CMDP

قیدهای ایمنی **وزن نمی‌گیرند، حذف می‌کنند.** یک عمل که STOP را دور بزند نباید
«هزینهٔ خیلی زیاد» بگیرد — باید اصلاً در مجموعهٔ انتخاب نباشد. وزنِ بی‌نهایت با
عددِ شناور شکننده است؛ حذف از مجموعه نیست.

## واحدِ Cost

`cost_usd` در پلنِ فلت **ساختاراً صفر است** (`subscription: max` ⇒ `est_worst_case()=0`).
هر دو فراخوانِ فوگوی ۲۵ جولای `cost_usd: 0.0` ثبت شدند. اگر EFE را با دلار ببندی،
ترمِ سوم بی‌صدا حذف می‌شود.

واحدِ درستِ Cost در این ارگانیسم: **ثانیهٔ توجهِ مالک.** تنها منبعی که کمیاب است و صفر نمی‌شود.

stdlib-only.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

__all__ = [
    "Policy", "Constraint", "EFEConfig", "evaluate", "select",
    "BETA_EPISTEMIC_MAX", "OWNER_SECOND_COST",
]

# سقفِ سختِ کنجکاوی. حتی در بیشینه، epistemic نمی‌تواند risk را خنثی کند.
BETA_EPISTEMIC_MAX = 0.5
# هزینهٔ یک ثانیه توجهِ مالک، در واحدِ همان مقیاسی که risk در آن است.
OWNER_SECOND_COST = 0.002        # ⇒ یک کارتِ ۶۰ ثانیه‌ای ≈ ۰.۱۲ واحد


@dataclass(frozen=True)
class Policy:
    """یک کنشِ ممکنِ داخلی."""

    name: str
    risk: float
    """انتظارِ فاصله از حالتِ ترجیحی. [0,1] نرمال‌شده."""
    epistemic: float
    """کاهشِ ابهامِ موردانتظار (information gain). [0,1]."""
    owner_seconds: float = 0.0
    """چند ثانیه از توجهِ آری می‌خورد — واحدِ واقعیِ Cost."""
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Constraint:
    """قیدِ سخت. `ok(policy) is False` ⇒ policy از مجموعه حذف می‌شود."""

    name: str
    ok: Callable[[Policy], bool]
    why: str = ""


@dataclass(frozen=True)
class EFEConfig:
    gamma: float = 4.0
    """precisionِ policy (نقشِ دوپامین). بالا = قاطع‌تر، نه بی‌پرواتر."""
    beta_epistemic: float = 0.25
    """وزنِ کنجکاوی. به BETA_EPISTEMIC_MAX کلیپ می‌شود."""
    risk_weight: float = 1.0

    @property
    def beta_effective(self) -> float:
        return max(0.0, min(BETA_EPISTEMIC_MAX, float(self.beta_epistemic)))


def expected_free_energy(p: Policy, cfg: EFEConfig) -> float:
    """G(π) = w_r·risk − β·epistemic + cost(ثانیهٔ مالک)."""
    return (cfg.risk_weight * float(p.risk)
            - cfg.beta_effective * float(p.epistemic)
            + OWNER_SECOND_COST * float(p.owner_seconds))


def evaluate(policies: list[Policy], constraints: list[Constraint],
             cfg: EFEConfig | None = None) -> dict:
    """ارزیابیِ کامل: حذفِ قیدشکن‌ها، محاسبهٔ G، توزیعِ softmax."""
    cfg = cfg or EFEConfig()
    feasible, blocked = [], []
    for p in policies:
        bad = [c for c in constraints if not _safe_ok(c, p)]
        (blocked if bad else feasible).append(
            (p, [c.name for c in bad]) if bad else p)

    if not feasible:
        return {"schema": "efe.v1", "selected": None, "feasible": [],
                "blocked": [{"policy": p.name, "violated": v} for p, v in blocked],
                "reason": "همهٔ گزینه‌ها قید را شکستند — fail-closed، هیچ کنشی"}

    gs = [(p, expected_free_energy(p, cfg)) for p in feasible]
    gmin = min(g for _, g in gs)
    exps = [(p, math.exp(-cfg.gamma * (g - gmin))) for p, g in gs]
    z = sum(e for _, e in exps) or 1.0
    probs = {p.name: e / z for p, e in exps}
    best = min(gs, key=lambda t: t[1])[0]

    return {
        "schema": "efe.v1",
        "gamma": cfg.gamma, "beta_effective": cfg.beta_effective,
        "selected": best.name,
        "feasible": [{"policy": p.name, "G": round(g, 5),
                      "risk": p.risk, "epistemic": p.epistemic,
                      "owner_seconds": p.owner_seconds,
                      "p": round(probs[p.name], 4)} for p, g in gs],
        "blocked": [{"policy": p.name, "violated": v} for p, v in blocked],
    }


def select(policies: list[Policy], constraints: list[Constraint],
           cfg: EFEConfig | None = None) -> Policy | None:
    r = evaluate(policies, constraints, cfg)
    name = r.get("selected")
    return next((p for p in policies if p.name == name), None) if name else None


def _safe_ok(c: Constraint, p: Policy) -> bool:
    """قیدِ خراب = قیدِ شکسته. fail-closed."""
    try:
        return bool(c.ok(p))
    except Exception:                                 # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# قیدهای استانداردِ اکتاپوس (§۲ KERNEL) — به‌صورتِ داده، نه کد پراکنده
# ---------------------------------------------------------------------------
def kernel_constraints(*, stop_present: bool, budget_frozen: bool,
                       owner_verdict_available: bool) -> list[Constraint]:
    """قیدهای تغییرناپذیر. هرکدام یک policy را **حذف** می‌کند، نه جریمه."""
    return [
        Constraint("STOP", lambda p: not (stop_present and p.meta.get("acts", False)),
                   "فایلِ STOP حاضر است ⇒ هیچ کنشی"),
        Constraint("BUDGET_FREEZE", lambda p: not (budget_frozen and p.meta.get("spends", False)),
                   "بودجه FREEZE است ⇒ هیچ خرجی"),
        Constraint("OUTWARD_NEEDS_OWNER",
                   lambda p: (not p.meta.get("outward", False)) or owner_verdict_available,
                   "اثرِ بیرونی بدونِ رأیِ مالک ممنوع"),
        Constraint("NO_TCB", lambda p: not p.meta.get("touches_tcb", False),
                   ".env / genome / kill-switch / budget — خطِ قرمزِ ثابت"),
        Constraint("PROPOSE_ONLY", lambda p: not p.meta.get("self_merge", False),
                   "C6 ساختاراً propose-only است"),
    ]
