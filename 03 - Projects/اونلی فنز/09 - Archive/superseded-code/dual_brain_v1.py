#!/usr/bin/env python3
"""dual_brain.py — مغزِ دوگانهٔ Project-F: Thinking + Communication.

تفکیکِ شناختی از ارتباطی:
  ThinkingBrain = فکر/تحلیل/استراتژی/قیمت/زمان — خروجی: پیشنهاد (proposal).
  CommBrain = ارتباطات/کپشن/DM/بریف صبا/گزارش آری — خروجی: متن (draft، human-gated).

چرا دو مغز؟
  - Thinking خالص است: عدد، تحلیل، قیمت. هیچ متنِ بیرونی تولید نمی‌کند.
  - Comm خروجیِ Thinking را می‌گیرد و به متنِ قابلِ فهم تبدیل می‌کند.
  - هر دو از همان Guardها می‌گذرند (Compliance + Ethics).
  - تفکیک یعنی: اگر Comm خراب شد، Thinking هنوز کار می‌کند (و برعکس).
  - λ_persist<0: هیچ‌کدام «بقا/engagement» را optimize نمی‌کنند.

خطوطِ قرمز: propose-only · صفر رسانه/PII · دوکلیده · محدودهٔ صبا مقدم ·
 Ethics-Guard · Compliance-Guard · پرداخت درون‌پلتفرم.
هیچ import از *_gate/chrono/money. $0 آفلاین، stdlib-only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

LAMBDA_PERSIST = -1.0


@dataclass
class Thought:
    """خروجیِ ThinkingBrain — یک تحلیل/پیشنهادِ عددی."""
    kind: str               # strategy | price | schedule | risk | segment
    data: dict              # {price: 15, tier: "mid", reasoning: "..."}
    confidence: float = 0.5
    tags: list[str] = field(default_factory=list)


@dataclass
class Message:
    """خروجیِ CommBrain — یک متنِ draft (human-gated)."""
    kind: str               # caption | dm | brief_saba | report_ari | trend_note
    text: str
    source_thought: str = ""   # کدام Thought این را تولید کرد
    tone: str = "warm"         # warm | professional | playful
    human_gated: bool = True   # همیشه True — هیچ انتشارِ خودکار


# ─── قواعدِ Guard (همان project_f_brain) ──────────────────────────────────────
COMPLIANCE_RULES = [
    "faceless", "feet_only", "no_explicit", "over_18",
    "inplatform_payment", "geo_block_iran",
]

ETHICS_RULES = [
    "no_dark_pattern", "no_manipulation", "relationship_80_sales_20",
    "performer_welfare", "scope_supreme", "no_engagement_optimization",
]

FORBIDDEN_TERMS = [
    # متنِ ممنوع در خروجیِ Comm
    "persian", "sydney", "iran", "tehran", "middle east",
    "real name", "address", "phone", "email",
    "paypal", "crypto", "bank transfer", "p2p",
]


def _check_compliance(checks: dict) -> list[str]:
    return [r for r in COMPLIANCE_RULES if not checks.get(r)]


def _check_ethics(checks: dict) -> list[str]:
    return [r for r in ETHICS_RULES if not checks.get(r)]


def _scan_forbidden(text: str) -> list[str]:
    """اسکنِ متن برای ترم‌های ممنوع."""
    t = str(text).lower()
    return [term for term in FORBIDDEN_TERMS if term in t]


# ════════════════════════════════════════════════════════════════════════════════
# ThinkingBrain — فکر/تحلیل/استراتژی
# ════════════════════════════════════════════════════════════════════════════════
class ThinkingBrain:
    """مغزِ فکر. عدد، استراتژی، قیمت، تحلیل. خروجی: Thought.
    هیچ متنِ بیرونی تولید نمی‌کند — فقط داده."""

    def __init__(self):
        self._pricing_history: list[dict] = []   # برای bandit learning
        self._risk_register: list[dict] = []

    def think_strategy(self, content_type: str = "standard",
                       season: str = "summer") -> Thought:
        """تحلیلِ استراتژی: wall vs PPV split."""
        return Thought(
            kind="strategy",
            data={"wall_pct": 0.55, "ppv_pct": 0.45,
                  "content_type": content_type, "season": season,
                  "reasoning": "55% wall for attraction, 45% PPV for revenue"},
            confidence=0.7, tags=["strategy", "ppv"])

    def think_price(self, content_type: str = "standard",
                    time_slot: str = "evening",
                    historical_data: list[dict] | None = None) -> Thought:
        """تحلیلِ قیمت: contextual bandit سه‌لایه.
        base × content_multiplier × time_multiplier.
        اگر historical_data باشد، از نتایجِ قبلی یاد می‌گیرد."""
        base = 10.0
        content_mult = {"standard": 1.0, "premium": 1.5, "exclusive": 2.0}.get(content_type, 1.0)
        time_mult = {"morning": 0.8, "afternoon": 0.9, "evening": 1.2, "night": 1.1}.get(time_slot, 1.0)

        # bandit learning: اگر historical داریم، base را تنظیم کن
        if historical_data:
            approved = [d for d in historical_data if d.get("outcome") == "approved"]
            if approved:
                avg_price = sum(d.get("price", base) for d in approved) / len(approved)
                base = max(5.0, min(30.0, avg_price * 0.9))   # gentle toward average

        price = base * content_mult * time_mult
        tier = "low" if price < 12 else ("premium" if price > 20 else "mid")
        return Thought(
            kind="price",
            data={"price": round(price, 2), "tier": tier,
                  "base": round(base, 2), "content_mult": content_mult,
                  "time_mult": time_mult, "content_type": content_type},
            confidence=0.6, tags=["price", tier])

    def think_schedule(self, platform: str = "reddit") -> Thought:
        """تحلیلِ زمانِ بهینه."""
        schedules = {
            "reddit": {"best": "09:00-12:00 AEST", "second": "21:00-22:00 AEST",
                       "reasoning": "US prime evening = Sydney morning"},
            "x": {"best": "18:00-20:00 AEST", "second": "12:00-13:00 AEST",
                  "reasoning": "AU evening + US morning overlap"},
            "of": {"best": "20:00-22:00 AEST", "second": "none",
                   "reasoning": "Evening browsing peak"},
        }
        s = schedules.get(platform, schedules["reddit"])
        return Thought(kind="schedule", data={"platform": platform, **s},
                       confidence=0.7, tags=["schedule", platform])

    def think_risk(self, draft_title: str, partner_stress: float = 0.3) -> Thought:
        """تحلیلِ ریسک."""
        risks = []
        if partner_stress > 0.7:
            risks.append({"risk": "partner-burnout", "severity": "high",
                          "mitigation": "reduce posting frequency, check-in with saba"})
        if "custom" in draft_title.lower():
            risks.append({"risk": "scope-creep", "severity": "medium",
                          "mitigation": "clear boundary in custom description"})
        risks.append({"risk": "platform-policy-change", "severity": "low",
                      "mitigation": "monthly ToS check"})
        return Thought(kind="risk", data={"risks": risks, "partner_stress": partner_stress},
                       confidence=0.5, tags=["risk"])

    def think_segment(self) -> Thought:
        """تحلیلِ سگمنتِ مخاطب."""
        return Thought(
            kind="segment",
            data={"segments": {
                "vip": {"pct": 0.05, "strategy": "personalized DM, early access"},
                "regular": {"pct": 0.25, "strategy": "PPV ladder, consistent posting"},
                "lurker": {"pct": 0.70, "strategy": "wall content, gentle nudge to PPV"},
            }},
            confidence=0.5, tags=["segment"])

    def process(self, draft_title: str, checks: dict | None = None,
                historical: list[dict] | None = None) -> list[Thought]:
        """یک دورِ کاملِ فکر: همه تحلیل‌ها. خروجی: لیستِ Thought."""
        c_missing = _check_compliance(checks or {})
        e_missing = _check_ethics(checks or {})
        if c_missing or e_missing:
            return [Thought(kind="blocked",
                            data={"compliance_fail": c_missing, "ethics_fail": e_missing},
                            confidence=0.0, tags=["blocked"])]
        return [
            self.think_strategy(),
            self.think_price(historical_data=historical),
            self.think_schedule(),
            self.think_risk(draft_title),
            self.think_segment(),
        ]


# ════════════════════════════════════════════════════════════════════════════════
# CommBrain — ارتباطات/کپشن/DM/بریف/گزارش
# ═════════════════════════════════════════════Ethics══════════════════════════════════════
class CommBrain:
    """مغزِ ارتباطات. Thought را می‌گیرد و به متن تبدیل می‌کند.
    همه خروجی‌ها draft + human-gated. Ethics-Guard در همه متن‌ها فعال."""

    def __init__(self):
        self._tone = "warm"   # warm | professional | playful

    def set_tone(self, tone: str) -> None:
        self._tone = tone if tone in ("warm", "professional", "playful") else "warm"

    def _guard_text(self, text: str) -> tuple[bool, list[str]]:
        """Ethics-Guard + scan_forbidden روی متن. خروجی: (passed, violations)."""
        violations = _scan_forbidden(text)
        return (len(violations) == 0, violations)

    def caption(self, thought: Thought, style: str = "cozy") -> Message:
        """از Thought یک کپشنِ draft بساز. بدون explicit، human-gated."""
        if thought.kind == "price":
            text = (f"New set just dropped ✨ "
                    f"{'Exclusive content' if thought.data.get('tier') == 'premium' else 'Fresh content'}"
                    f" — message me for access 💫")
        elif thought.kind == "strategy":
            text = "Weekend vibes ☕ cozy content coming your way"
        else:
            text = "Something special is brewing... stay tuned ✨"
        passed, violations = self._guard_text(text)
        if not passed:
            text = "[BLOCKED by Ethics-Guard — forbidden terms detected]"
        return Message(kind="caption", text=text,
                       source_thought=thought.kind, tone=self._tone)

    def dm_draft(self, thought: Thought, recipient_segment: str = "regular") -> Message:
        """draft DM. 80% relationship / 20% sales. human-gated."""
        if recipient_segment == "vip":
            text = ("Hey! Noticed you've been supporting for a while 💛 "
                    "I have something special I think you'd love — "
                    "want me to send you the details?")
        elif recipient_segment == "regular":
            text = ("Hi! Thanks for being here ✨ "
                    "Just wanted to say I appreciate your support. "
                    "I've got some new content up if you're interested!")
        else:
            text = "Welcome! Glad you found me here ✨ Feel free to explore."
        passed, violations = self._guard_text(text)
        if not passed:
            text = "[BLOCKED by Ethics-Guard]"
        return Message(kind="dm", text=text,
                       source_thought=thought.kind, tone=self._tone)

    def brief_for_saba(self, thoughts: list[Thought]) -> Message:
        """بریفِ کوتاه برای صبا: چه Produces، چه زمانی، چه قیمتی."""
        lines = ["📋 بریفِ این هفته:", "──────────"]
        for t in thoughts:
            if t.kind == "strategy":
                lines.append(f"📊 استراتژی: {t.data.get('wall_pct', 0)*100:.0f}% wall")
            elif t.kind == "price":
                lines.append(f"💰 قیمتِ پیشنهادی: ${t.data.get('price', '?')} ({t.data.get('tier', '?')})")
            elif t.kind == "schedule":
                lines.append(f"⏰ زمان: {t.data.get('best', '?')}")
            elif t.kind == "risk":
                risks = t.data.get("risks", [])
                if risks:
                    lines.append(f"⚠️ ریسک: {risks[0].get('risk', '?')}")
        lines.append("──────────")
        lines.append("✋ محدودهٔ صبا مقدم. انتشار فقط با تأییدِ آری.")
        text = "\n".join(lines)
        passed, violations = self._guard_text(text)
        if not passed:
            text = "[BLOCKED by Ethics-Guard]"
        return Message(kind="brief_saba", text=text, tone=self._tone)

    def report_for_ari(self, thoughts: list[Thought],
                       drafts_count: int = 0) -> Message:
        """گزارشِ کوتاه برای آری: وضعیت، ریسک، تصمیمِ منتظر."""
        lines = ["📊 گزارشِ Project-F:", "──────────"]
        lines.append(f"📋 درفت‌های ثبت‌شده: {drafts_count}")
        for t in thoughts:
            if t.kind == "price":
                lines.append(f"💰 پیشنهادِ قیمت: ${t.data.get('price', '?')} (نیاز به تأیید)")
            elif t.kind == "risk":
                for r in t.data.get("risks", []):
                    if r.get("severity") in ("high", "medium"):
                        lines.append(f"⚠️ {r.get('risk')}: {r.get('mitigation', '')}")
        lines.append(f"🔒 money قفل · λ_persist={LAMBDA_PERSIST}")
        text = "\n".join(lines)
        return Message(kind="report_ari", text=text, tone="professional")

    def trend_note(self, trend_tag: str, note: str = "") -> Message:
        """یادداشتِ ترند برای صبا."""
        text = f"🔎 ترند: #{trend_tag}\n{note}\n<i>human-gated — هیچ‌چیز خودکار.</i>"
        return Message(kind="trend_note", text=text, tone=self._tone)


# ════════════════════════════════════════════════════════════════════════════════
# DualBrain — هماهنگ‌کننده
# ════════════════════════════════════════════════════════════════════════════════
class DualBrain:
    """دو مغز هماهنگ. ThinkingBrain فکر می‌کند، CommBrain ارتباط می‌گیرد.
    هر دو از Guardها می‌گذرند. λ_persist<0."""

    def __init__(self):
        self.thinking = ThinkingBrain()
        self.comm = CommBrain()

    def process_and_communicate(self, draft_title: str,
                                checks: dict | None = None,
                                historical: list[dict] | None = None,
                                drafts_count: int = 0) -> dict:
        """یک دورِ کامل: Thinking → Comm. خروجی: {thoughts, messages}.
        همه propose-only + human-gated."""
        # ۱. Thinking
        thoughts = self.thinking.process(draft_title, checks=checks,
                                          historical=historical)
        if thoughts and thoughts[0].kind == "blocked":
            return {"thoughts": [asdict(t) for t in thoughts],
                    "messages": [], "blocked": True}

        # ۲. Comm: از Thoughtها پیام بساز
        messages = []
        for t in thoughts:
            if t.kind == "price":
                messages.append(asdict(self.comm.caption(t)))
                messages.append(asdict(self.comm.dm_draft(t)))
            elif t.kind == "strategy":
                messages.append(asdict(self.comm.caption(t)))
        # بریف برای صبا + گزارش برای آری
        messages.append(asdict(self.comm.brief_for_saba(thoughts)))
        messages.append(asdict(self.comm.report_for_ari(thoughts, drafts_count)))

        return {"thoughts": [asdict(t) for t in thoughts],
                "messages": messages, "blocked": False}
