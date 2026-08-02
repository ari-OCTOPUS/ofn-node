#!/usr/bin/env python3
"""dual_brain_v3.py — مغزِ دوگانهٔ Project-F (نسخه‌ی عمیق).

ThinkingBrain — ۱۰ ساب‌عامل تخصصی:
  1. Strategist   — استراتژیِ نردبانِ ارزش (wall vs PPV)
  2. Pricer       — قیمت‌گذاریِ contextual-bandit (یادگیر)
  3. Scheduler    — زمان‌بندیِ بهینه
  4. RiskAnalyzer — تحلیلِ ریسک
  5. Segmenter    — سگمنت‌بندیِ مخاطب
  6. CompetitorIntel — تحلیلِ رقبا (aggregate)
  7. TrendForecaster — پیش‌بینیِ ترند
  8. RetentionStrategist — استراتژیِ نگهداشت
  9. ContentOptimizer — بهینه‌سازیِ نوعِ محتوا
  10. FunnelAnalyst — تحلیلِ قیفِ تبدیل

CommBrain — ۷ نوعِ خروجیِ متنی:
  caption / dm / brief_saba / report_ari / trend_note / retention_dm / ab_announcement

هر دو از Ethics-Guard می‌گذرند. λ_persist<0. همه human-gated.
هیچ import از *_gate/chrono/money. $0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from collections import defaultdict

LAMBDA_PERSIST = -1.0

# denylist دوزبانه (لاتین + فارسی/فینگلیش).
# چرا دوزبانه (لِین B · 2026-08-03): تطبیق substring روی `.lower()` است و
# `str.lower()` روی فارسی بی‌اثر — پس تا امروز «Sydney» بلاک می‌شد ولی «سیدنی»
# از همین فیلتر رد می‌شد، یعنی قاعدهٔ #۶ (هیچ فکتِ جغرافیایی در حدِ شهر، هیچ
# سیگنالِ متنیِ قومی) در برابرِ ورودیِ فارسی بی‌دندان بود — و ورودیِ فارسی در
# این ونچر حالتِ عادی است نه لبه.
# عمداً **نیست**: «استرالیا / استرالیایی / Aussie» — کشوری‌اند و طبقِ
# VOICE-AND-STYLE مجاز؛ بن‌کردنشان over-blocking است.
FORBIDDEN_TERMS = [
    "persian", "sydney", "iran", "tehran", "middle east",
    "real name", "address", "phone", "email",
    "paypal", "crypto", "bank transfer", "p2p",
    # ── شهر/جغرافیا (پاریتهٔ sydney/tehran/middle east) ──
    "تهران", "خاورمیانه", "سیدنی", "sidney", "sydeny",
    # ── قومیت/زبان (پاریتهٔ persian) ──
    "ایران", "ایرانی", "پارسی", "پرشین", "فارسی", "farsi", "irani", "persion",
    # ── نامِ پلتفرم (containment) ──
    "انلی فنز", "اونلی فنز", "اونلی‌فنز", "فنسلی",
    # ── PII (پاریتهٔ real name/address/phone/email) ──
    "آدرس", "اسم واقعی", "ایمیل", "شماره تلفن", "نام واقعی",
    # ── مسیرِ پرداختِ خارج‌پلتفرم (پاریتهٔ paypal/crypto/bank transfer) ──
    "بیت کوین", "بیت‌کوین", "پی پال", "پی‌پال", "پیپال", "حواله",
    "رمزارز", "کارت به کارت", "کریپتو",
]

# نرمال‌سازِ سبکِ فارسی — خالص، stdlib، بدونِ وابستگی.
# لازم است چون فهرست بالا نمی‌تواند همهٔ املاهای «ی/ک عربی» را برشمارد:
# «سيدني» چهار ترکیب دارد و «ایرانی» هم چهار. نگاشت روی حروفِ لاتین بی‌اثر است،
# پس رفتارِ امروزِ واژه‌های لاتین بایت‌به‌بایت دست‌نخورده می‌ماند.
_FA_TRANS = str.maketrans({
    "ي": "ی",   # ي عربی → ی فارسی
    "ى": "ی",   # ى الف مقصوره → ی فارسی
    "ك": "ک",   # ك عربی → ک فارسی
    "‌": "",         # نیم‌فاصله (ZWNJ)
    "ـ": "",         # کشیده (tatweel)
})


def fa_norm(text: str) -> str:
    """کوچک‌سازی + یکسان‌سازیِ ی/ک عربی + حذفِ نیم‌فاصله/کشیده (برای تطبیقِ denylist)."""
    return str(text or "").translate(_FA_TRANS).lower()

COMPLIANCE_RULES = [
    "faceless", "feet_only", "no_explicit", "over_18",
    "inplatform_payment", "geo_block_iran",
]

ETHICS_RULES = [
    "no_dark_pattern", "no_manipulation", "relationship_80_sales_20",
    "performer_welfare", "scope_supreme", "no_engagement_optimization",
]


@dataclass
class Thought:
    kind: str
    data: dict
    confidence: float = 0.5
    tags: list[str] = field(default_factory=list)
    source_agent: str = ""


@dataclass
class Message:
    kind: str
    text: str
    source_thought: str = ""
    tone: str = "warm"
    human_gated: bool = True
    platform: str = ""


def _guard_text(text: str) -> tuple[bool, list[str]]:
    t = fa_norm(text)
    violations = [term for term in FORBIDDEN_TERMS if fa_norm(term) in t]
    return (len(violations) == 0, violations)


def _checks_pass(checks: dict) -> bool:
    return all(checks.get(r) for r in COMPLIANCE_RULES + ETHICS_RULES)


# ════════════════════════════════════════════════════════════════════════════════
# ThinkingBrain — ۱۰ ساب‌عامل
# ════════════════════════════════════════════════════════════════════════════════
class ThinkingBrain:
    """مغزِ فکر. ۱۰ ساب‌عاملِ تخصصی. خروجی: Thought (داده، نه متن)."""

    def __init__(self, historical: list[dict] | None = None):
        self._historical = historical or []
        self._pricing_history = [d for d in self._historical if d.get("type") == "price"]
        self._post_history = [d for d in self._historical if d.get("type") == "post"]

    # 1. Strategist
    def strategist(self, content_type: str = "standard", season: str = "summer") -> Thought:
        wall = 0.55 if content_type == "standard" else 0.40
        return Thought(kind="strategy", source_agent="Strategist",
            data={"wall_pct": wall, "ppv_pct": round(1 - wall, 2),
                  "content_type": content_type, "season": season,
                  "reasoning": f"{wall*100:.0f}% wall for attraction"},
            confidence=0.7, tags=["strategy"])

    # 2. Pricer (contextual bandit — یادگیر)
    def pricer(self, content_type: str = "standard", time_slot: str = "evening") -> Thought:
        base = 10.0
        c_mult = {"standard": 1.0, "premium": 1.5, "exclusive": 2.0}.get(content_type, 1.0)
        t_mult = {"morning": 0.8, "afternoon": 0.9, "evening": 1.2, "night": 1.1}.get(time_slot, 1.0)
        if self._pricing_history:
            approved = [d for d in self._pricing_history if d.get("outcome") == "approved"]
            if approved:
                avg = sum(d.get("price", base) for d in approved) / len(approved)
                base = max(5.0, min(30.0, avg * 0.9))
        price = base * c_mult * t_mult
        tier = "low" if price < 12 else ("premium" if price > 20 else "mid")
        return Thought(kind="price", source_agent="Pricer",
            data={"price": round(price, 2), "tier": tier, "base": round(base, 2),
                  "content_mult": c_mult, "time_mult": t_mult},
            confidence=0.6, tags=["price", tier])

    # 3. Scheduler
    def scheduler(self, platform: str = "reddit") -> Thought:
        schedules = {
            "reddit": {"best": "09:00-12:00 AEST", "second": "21:00-22:00"},
            "x": {"best": "18:00-20:00 AEST", "second": "12:00-13:00"},
            "of": {"best": "20:00-22:00 AEST", "second": "none"},
        }
        s = schedules.get(platform, schedules["reddit"])
        return Thought(kind="schedule", source_agent="Scheduler",
            data={"platform": platform, **s}, confidence=0.7, tags=["schedule"])

    # 4. RiskAnalyzer
    def risk_analyzer(self, draft_title: str = "", partner_stress: float = 0.3) -> Thought:
        risks = []
        if partner_stress > 0.7:
            risks.append({"risk": "partner-burnout", "severity": "high",
                          "mitigation": "reduce frequency, check-in"})
        if "custom" in draft_title.lower():
            risks.append({"risk": "scope-creep", "severity": "medium",
                          "mitigation": "clear boundary description"})
        risks.append({"risk": "platform-policy-change", "severity": "low",
                      "mitigation": "monthly ToS check"})
        if len(self._post_history) < 5:
            risks.append({"risk": "insufficient-data", "severity": "medium",
                          "mitigation": "post more for learning"})
        return Thought(kind="risk", source_agent="RiskAnalyzer",
            data={"risks": risks, "count": len(risks),
                  "highest": max((r["severity"] for r in risks), default="none")},
            confidence=0.5, tags=["risk"])

    # 5. Segmenter
    def segmenter(self) -> Thought:
        return Thought(kind="segment", source_agent="Segmenter",
            data={"segments": {
                "vip": {"pct": 0.05, "strategy": "personalized DM, early access"},
                "regular": {"pct": 0.25, "strategy": "PPV ladder"},
                "lurker": {"pct": 0.70, "strategy": "wall content, gentle nudge"}}},
            confidence=0.5, tags=["segment"])

    # 6. CompetitorIntel
    def competitor_intel(self, competitor_data: list[dict] | None = None) -> Thought:
        data = competitor_data or []
        if not data:
            return Thought(kind="competitor", source_agent="CompetitorIntel",
                data={"status": "no_data"}, confidence=0.1, tags=["competitor"])
        by_tag: dict[str, list[float]] = defaultdict(list)
        for c in data:
            by_tag[c.get("tag", "?")].append(c.get("avg_upvotes", 0))
        hot = {tag: sum(v) / len(v) for tag, v in by_tag.items()}
        return Thought(kind="competitor", source_agent="CompetitorIntel",
            data={"hot_tags": dict(sorted(hot.items(), key=lambda x: -x[1])[:5]),
                  "total_competitors": len(data)},
            confidence=0.6, tags=["competitor"])

    # 7. TrendForecaster
    def trend_forecaster(self, season: str = "summer") -> Thought:
        seasonal_trends = {
            "summer": ["sandals", "beach-feet", "bright-pedicure"],
            "autumn": ["boots", "cozy-socks", "warm-tones"],
            "winter": ["fuzzy-socks", "indoor-cozy", "spa-pedicure"],
            "spring": ["floral", "fresh-pedicure", "sandals-return"],
        }
        trends = seasonal_trends.get(season, seasonal_trends["summer"])
        return Thought(kind="trend", source_agent="TrendForecaster",
            data={"predicted_trends": trends, "season": season,
                  "horizon": "4-6 weeks"},
            confidence=0.4, tags=["trend", season])

    # 8. RetentionStrategist
    def retention_strategist(self, churn_rate: float = 0.27) -> Thought:
        actions = []
        if churn_rate > 0.3:
            actions.append({"action": "increase wall content frequency",
                            "reason": "churn above target"})
        actions.append({"action": "win-back DM for lapsed subscribers (>14 days)",
                        "reason": "standard retention"})
        if churn_rate < 0.25:
            actions.append({"action": "test PPV price increase",
                            "reason": "low churn = pricing power"})
        return Thought(kind="retention", source_agent="RetentionStrategist",
            data={"churn_rate": churn_rate, "actions": actions},
            confidence=0.5, tags=["retention"])

    # 9. ContentOptimizer
    def content_optimizer(self, post_history: list[dict] | None = None) -> Thought:
        history = post_history or self._post_history
        if not history:
            return Thought(kind="content_opt", source_agent="ContentOptimizer",
                data={"status": "no_data", "suggestion": "test 3 different styles"},
                confidence=0.1, tags=["content"])
        by_tag: dict[str, list[float]] = defaultdict(list)
        for p in history:
            tag = p.get("tag", "?")
            score = p.get("upvotes", 0) / 100 + p.get("comments", 0) / 20
            by_tag[tag].append(min(1.0, score))
        ranked = {tag: sum(v) / len(v) for tag, v in by_tag.items()}
        best = max(ranked, key=ranked.get) if ranked else None
        worst = min(ranked, key=ranked.get) if ranked else None
        return Thought(kind="content_opt", source_agent="ContentOptimizer",
            data={"best_tag": best, "worst_tag": worst,
                  "all_scores": ranked,
                  "suggestion": f"focus {best}, reduce {worst}" if best and worst else "collect more data"},
            confidence=min(0.8, len(history) / 15))

    # 10. FunnelAnalyst
    def funnel_analyst(self, visitors: int = 100, subscribers: int = 5,
                       ppv_buyers: int = 1) -> Thought:
        sub_rate = subscribers / max(visitors, 1)
        ppv_rate = ppv_buyers / max(subscribers, 1)
        bottlenecks = []
        if sub_rate < 0.05:
            bottlenecks.append({"stage": "visitor→subscriber", "rate": sub_rate,
                                "fix": "improve wall content + bio"})
        if ppv_rate < 0.2:
            bottlenecks.append({"stage": "subscriber→PPV buyer", "rate": ppv_rate,
                                "fix": "improve PPV value proposition"})
        return Thought(kind="funnel", source_agent="FunnelAnalyst",
            data={"visitor→sub_rate": round(sub_rate, 3),
                  "sub→ppv_rate": round(ppv_rate, 3),
                  "bottlenecks": bottlenecks},
            confidence=0.6, tags=["funnel"])

    def process_all(self, draft_title: str = "", checks: dict | None = None,
                    competitor_data: list[dict] | None = None,
                    post_history: list[dict] | None = None,
                    visitors: int = 100, subscribers: int = 5,
                    ppv_buyers: int = 1, partner_stress: float = 0.3,
                    season: str = "summer") -> list[Thought]:
        """همهٔ ۱۰ ساب‌عامل. اگر guard fail → فقط [blocked]."""
        if not _checks_pass(checks or {}):
            return [Thought(kind="blocked", data={"reason": "guard fail"},
                            confidence=0, tags=["blocked"])]
        return [
            self.strategist(season=season),
            self.pricer(),
            self.scheduler(),
            self.risk_analyzer(draft_title, partner_stress),
            self.segmenter(),
            self.competitor_intel(competitor_data),
            self.trend_forecaster(season),
            self.retention_strategist(),
            self.content_optimizer(post_history),
            self.funnel_analyst(visitors, subscribers, ppv_buyers),
        ]


# ════════════════════════════════════════════════════════════════════════════════
# CommBrain — ۷ نوعِ خروجی
# ════════════════════════════════════════════════════════════════════════════════
class CommBrain:
    """مغزِ ارتباطات. Thought→Message. Ethics-Guard. human-gated."""

    def __init__(self):
        self._tone = "warm"

    def set_tone(self, tone: str) -> None:
        self._tone = tone if tone in ("warm", "professional", "playful") else "warm"

    def _safe(self, text: str) -> str:
        passed, violations = _guard_text(text)
        return text if passed else f"[BLOCKED by Ethics-Guard: {violations}]"

    def caption(self, thought: Thought, style: str = "cozy") -> Message:
        if thought.kind == "price":
            tier = thought.data.get("tier", "mid")
            text = ("✨ New exclusive set just dropped! " if tier == "premium"
                    else "☕ Fresh cozy content — come take a look ✨")
        elif thought.kind == "strategy":
            text = "Weekend vibes ☕ Something cozy coming your way 💫"
        elif thought.kind == "trend":
            trends = thought.data.get("predicted_trends", [])
            text = f"Fresh look incoming ✨ {trends[0] if trends else 'cozy vibes'} this week"
        else:
            text = "Something special is brewing ✨ stay tuned"
        return Message(kind="caption", text=self._safe(text),
                       source_thought=thought.kind, tone=self._tone, platform="reddit")

    def dm_draft(self, thought: Thought, segment: str = "regular") -> Message:
        if segment == "vip":
            text = ("Hey! 💛 Noticed you've been here a while. "
                    "I've got something special — want me to send details?")
        elif segment == "regular":
            text = ("Hi! Thanks for being here ✨ Appreciate your support. "
                    "New content is up if you're interested!")
        else:
            text = "Welcome! Glad you found me ✨ Feel free to explore."
        return Message(kind="dm", text=self._safe(text),
                       source_thought=thought.kind, tone=self._tone)

    def brief_for_saba(self, thoughts: list[Thought]) -> Message:
        lines = ["📋 بریفِ این هفته:", "──────────"]
        for t in thoughts:
            if t.kind == "strategy":
                lines.append(f"📊 استراتژی: {t.data.get('wall_pct',0)*100:.0f}% wall")
            elif t.kind == "price":
                lines.append(f"💰 قیمت: ${t.data.get('price','?')} ({t.data.get('tier','?')})")
            elif t.kind == "schedule":
                lines.append(f"⏰ زمان: {t.data.get('best','?')}")
            elif t.kind == "risk":
                lines.append(f"⚠️ ریسکِ بالا: {t.data.get('highest','none')}")
            elif t.kind == "trend":
                trends = t.data.get("predicted_trends", [])
                if trends:
                    lines.append(f"📌 ترندِ فصل: {trends[0]}")
            elif t.kind == "content_opt":
                lines.append(f"🎯 بهترین محتوا: {t.data.get('best_tag','?')}")
            elif t.kind == "funnel":
                bn = t.data.get("bottlenecks", [])
                if bn:
                    lines.append(f"🔗 گلوگاه: {bn[0].get('stage','?')}")
            elif t.kind == "retention":
                acts = t.data.get("actions", [])
                if acts:
                    lines.append(f"🔄 نگهداشت: {acts[0].get('action','?')}")
            elif t.kind == "competitor":
                hot = t.data.get("hot_tags", {})
                if hot:
                    lines.append(f"🔍 رقبا: {list(hot.keys())[:2]}")
        lines.append("──────────")
        lines.append("✋ محدودهٔ صبا مقدم. انتشار با تأییدِ آری.")
        return Message(kind="brief_saba", text=self._safe("\n".join(lines)),
                       tone=self._tone)

    def report_for_ari(self, thoughts: list[Thought],
                       drafts_count: int = 0) -> Message:
        lines = ["📊 گزارشِ Project-F:", "──────────"]
        lines.append(f"📋 درفت‌ها: {drafts_count}")
        for t in thoughts:
            if t.kind == "price":
                lines.append(f"💰 قیمت: ${t.data.get('price','?')} (نیاز به تأیید)")
            elif t.kind == "risk":
                for r in t.data.get("risks", []):
                    if r.get("severity") in ("high", "medium"):
                        lines.append(f"⚠️ {r['risk']}: {r.get('mitigation','')}")
            elif t.kind == "funnel":
                lines.append(f"🔗 تبدیل: vis→sub {t.data.get('visitor→sub_rate',0)*100:.1f}% · sub→PPV {t.data.get('sub→ppv_rate',0)*100:.1f}%")
        lines.append(f"🔒 money قفل · λ_persist={LAMBDA_PERSIST}")
        return Message(kind="report_ari", text=self._safe("\n".join(lines)),
                       tone="professional")

    def trend_note(self, trends: list[str]) -> Message:
        lines = ["🔎 ترندهای پیش‌بینی‌شده:", "──────────"]
        for t in trends:
            lines.append(f"📌 {t}")
        lines.append("<i>human-gated</i>")
        return Message(kind="trend_note", text=self._safe("\n".join(lines)), tone=self._tone)

    def retention_dm(self, segment: str, days_lapsed: int = 0) -> Message:
        if days_lapsed > 14:
            text = ("Hey, miss me? 💛 Back with fresh content — "
                    "would love to have you again ✨")
        else:
            text = "Thanks for sticking around 💛 New content dropping soon!"
        return Message(kind="retention_dm", text=self._safe(text), tone=self._tone)

    def ab_announcement(self, variant_a: str, variant_b: str) -> Message:
        text = (f"🧪 A/B test this week:\n"
                f"A: {variant_a}\nB: {variant_b}\n"
                f"<i>Both drafted — you choose which to post.</i>")
        return Message(kind="ab", text=self._safe(text), tone=self._tone)


# ════════════════════════════════════════════════════════════════════════════════
# DualBrainV3 — هماهنگ‌کننده
# ════════════════════════════════════════════════════════════════════════════════
class DualBrainV3:
    """نسخه‌ی عمیق: ۱۰ ThinkingAgent + ۷ CommOutput.
    SprintContract + HookBus integration-ready."""

    def __init__(self, historical: list[dict] | None = None):
        self.thinking = ThinkingBrain(historical=historical)
        self.comm = CommBrain()

    def think_and_communicate(self, draft_title: str = "",
                               checks: dict | None = None,
                               competitor_data: list[dict] | None = None,
                               post_history: list[dict] | None = None,
                               visitors: int = 100, subscribers: int = 5,
                               ppv_buyers: int = 1, partner_stress: float = 0.3,
                               season: str = "summer",
                               drafts_count: int = 0) -> dict:
        """دورِ کامل: ۱۰ agent فکر → Comm پیام. همه human-gated."""
        thoughts = self.thinking.process_all(
            draft_title=draft_title, checks=checks,
            competitor_data=competitor_data, post_history=post_history,
            visitors=visitors, subscribers=subscribers, ppv_buyers=ppv_buyers,
            partner_stress=partner_stress, season=season)
        if thoughts and thoughts[0].kind == "blocked":
            return {"thoughts": [asdict(t) for t in thoughts], "messages": [],
                    "blocked": True}
        messages = []
        for t in thoughts:
            if t.kind in ("price", "strategy", "trend"):
                messages.append(asdict(self.comm.caption(t)))
        messages.append(asdict(self.comm.brief_for_saba(thoughts)))
        messages.append(asdict(self.comm.report_for_ari(thoughts, drafts_count)))
        trend_thought = next((t for t in thoughts if t.kind == "trend"), None)
        if trend_thought:
            messages.append(asdict(self.comm.trend_note(
                trend_thought.data.get("predicted_trends", []))))
        return {"thoughts": [asdict(t) for t in thoughts],
                "messages": messages, "blocked": False}
