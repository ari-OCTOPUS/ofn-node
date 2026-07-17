#!/usr/bin/env python3
"""lead_scorer.py — موتورِ امتیازدهیِ لیدِ نقاشی (مرحلهٔ ۱ نقشهٔ لید، 2026-07-15).

پورتِ وفادارِ `_launchpad/second-brain-live/painting-bot/lead_scorer.py` به داخلِ
ارگانیسم: همان ریاضی (فیلترِ سخت → مسیریابیِ دسته → سیگنال‌های جمع‌پذیر → ارزش →
جغرافیا → آستانه‌ها)، ولی stdlib-فقط — وابستگیِ pyyaml حذف و کلِ
`painter_lead_scoring.yaml` عیناً به‌صورت DEFAULT_CONFIG این‌جا inline شد.
⚠️ هر تغییرِ وزن این‌جا باید آگاهانه باشد؛ تستِ test_lead_scorer.py مقادیر را به
مقادیرِ yamlِ اصلی پین کرده تا driftِ خاموش لو برود.

تابعِ خالص: dict-ورودی → ScoredLead-خروجی. هیچ I/O، هیچ شبکه، هیچ effector —
تصمیمِ نهایی (draft/save/skip) فقط یک «پیشنهاد» است؛ مصرف‌کننده (lead_discovery_beat)
propose-only است و ارسال همیشه human-gated می‌ماند.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# ─── کانفیگ — inlineِ عیناً painter_lead_scoring.yaml (فلسفه: فیلترِ سخت + مسیریابی
# بر اساسِ «نوعِ خریدار»؛ strata اول = رابطهٔ تکرارشونده) ───────────────────────────
DEFAULT_CONFIG: dict = {
    "meta": {
        "operator": "Sydney painter",
        "base_lat": -33.8688,          # مرکزِ سرویس (CBD سیدنی)
        "base_lng": 151.2093,
        "max_service_radius_km": 40,
    },
    "actions": {
        "draft_threshold": 70,          # ≥70 → draft (کاندیدِ propose)
        "save_threshold": 45,           # 45–69 → save؛ <45 → skip
    },
    "category_priority": [
        "strata_remedial",
        "government_education",
        "new_residential_multi",
        "commercial_fitout",
    ],
    "hard_skip": {
        "any_phrase": [
            "demolition only", "tree removal", "subdivision of land",
            "strata subdivision", "boundary adjustment",
            "torrens title subdivision", "swimming pool", "signage only",
        ],
        "single_dwelling_phrases": [
            "dwelling house", "single dwelling", "detached dwelling",
            "secondary dwelling", "granny flat",
        ],
        "single_dwelling_value_floor": 250000,
    },
    "categories": {
        "strata_remedial": {
            "base": 55,
            "label": "Strata remedial / common-property repaint",
            "required_any": [
                "common property", "owners corporation", "remedial",
                "render and paint", "render & paint", "balustrade", "balcony",
            ],
            "context_any": [
                "strata", "units", "apartments", "flat building",
                "multi dwelling", "multi-dwelling", "common property",
                "owners corporation",
            ],
        },
        "government_education": {
            "base": 35,
            "label": "Government / education / social housing (route to tenders)",
            "required_any": [
                "school", "tafe", "hospital", "health facility",
                "social housing", "community facility", "public building",
            ],
        },
        "new_residential_multi": {
            "base": 30,
            "label": "New multi-residential build (future client + builder relationship)",
            "required_any": [
                "residential flat building", "multi dwelling housing",
                "multi-dwelling housing", "apartment building", "townhouses",
                "shop top housing", "boarding house",
            ],
        },
        "commercial_fitout": {
            "base": 40,
            "label": "Commercial fitout / change of use (builder is the buyer)",
            "required_any": [
                "fitout", "fit out", "fit-out", "change of use",
                "retail premises", "office", "tenancy", "shopfront",
                "refurbishment",
            ],
        },
    },
    "signals": {
        "paint_scope": {
            "weight": 18,
            "any_phrase": [
                "paint", "repaint", "render", "coating", "external alteration",
                "internal alteration", "facade", "fitout", "fit out", "fit-out",
                "refurbishment",
            ],
        },
        "recurring_buyer": {
            "weight": 10,
            "any_phrase": [
                "common property", "owners corporation", "strata", "maintenance",
            ],
        },
        "red_flags": {
            "weight": -15,
            "any_phrase": [
                "business identification signage", "advertising",
                "illuminated sign", "awning", "heritage",
            ],
        },
    },
    "value_tiers": [
        {"min": 1000000, "bonus": 15},
        {"min": 300000, "bonus": 10},
        {"min": 100000, "bonus": 5},
        {"min": 0, "bonus": 0},
    ],
    "geo": {
        "in_radius_bonus": 8,
        "out_of_radius_penalty": -20,
    },
}


# ─── helpers ────────────────────────────────────────────────────────────────────
def _haystack(lead: dict) -> str:
    """متنِ lowercase که کلیدواژه‌ها در آن جستجو می‌شوند."""
    parts = [str(lead.get("description", "")), str(lead.get("address", ""))]
    return " ".join(parts).lower()


def _matches(haystack: str, phrases) -> list[str]:
    """عبارت‌هایی که به‌صورتِ substring در haystack هستند."""
    return [p for p in (phrases or []) if p.lower() in haystack]


def _haversine_km(lat1, lng1, lat2, lng2) -> float | None:
    if None in (lat1, lng1, lat2, lng2):
        return None
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ─── نتیجه ──────────────────────────────────────────────────────────────────────
@dataclass
class ScoredLead:
    category: str
    category_label: str
    score: int
    action: str                                   # "draft" | "save" | "skip"
    reasons: list[str] = field(default_factory=list)
    lead: dict = field(default_factory=dict)

    def card(self) -> str:
        """کارتِ تلگرامی — برای نمایشِ کاندیدا به مالک (مرحلهٔ ۷)."""
        L = self.lead
        emoji = {"draft": "🟢", "save": "🟡", "skip": "⚪️"}.get(self.action, "🏢")
        lines = [
            f"{emoji} {L.get('source', 'lead')} | score: {self.score} | {self.category}",
            f"📌 {str(L.get('description', '')).strip()}",
            f"📍 {L.get('address', 'n/a')}",
        ]
        if L.get("url"):
            lines.append(f"🔗 {L['url']}")
        lines.append("🧠 " + "; ".join(self.reasons))
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {"category": self.category, "category_label": self.category_label,
                "score": self.score, "action": self.action, "reasons": self.reasons}


# ─── امتیازدهنده ────────────────────────────────────────────────────────────────
class LeadScorer:
    """قطعی، $0، بدونِ I/O. کانفیگِ سفارشی فقط برای تست/تنظیم — پیش‌فرض همان yaml."""

    def __init__(self, config: dict | None = None):
        self.cfg = config or DEFAULT_CONFIG

    # -- فیلترهای سخت: اصابت = skip بی‌قیدوشرط --------------------------------------
    def _hard_skip(self, hay: str, lead: dict) -> str | None:
        hs = self.cfg["hard_skip"]
        hit = _matches(hay, hs.get("any_phrase"))
        if hit:
            return f"hard-skip ({hit[0]})"
        sd = _matches(hay, hs.get("single_dwelling_phrases"))
        if sd:
            cost = lead.get("cost_of_development")
            floor = hs.get("single_dwelling_value_floor", 0)
            if cost is not None and cost < floor:
                return f"single dwelling under ${floor:,} ({sd[0]})"
        return None

    # -- مسیریابیِ دسته (اولین اصابت برنده — strata عمداً اول) -----------------------
    def _route(self, hay: str) -> tuple[str, dict]:
        cats = self.cfg["categories"]
        for name in self.cfg["category_priority"]:
            c = cats[name]
            if not _matches(hay, c.get("required_any")):
                continue
            ctx = c.get("context_any")
            if ctx and not _matches(hay, ctx):
                continue
            return name, c
        return "uncategorised", {"base": 0, "label": "No clear paint-relevant scope"}

    # -- ارزش + جغرافیا -------------------------------------------------------------
    def _value_bonus(self, lead: dict) -> tuple[int, str | None]:
        cost = lead.get("cost_of_development")
        if cost is None:
            return 0, None
        for tier in self.cfg["value_tiers"]:
            if cost >= tier["min"]:
                if tier["bonus"]:
                    return tier["bonus"], f"value ${cost:,} (+{tier['bonus']})"
                return 0, None
        return 0, None

    def _geo_adjust(self, lead: dict) -> tuple[int, str | None]:
        m, g = self.cfg["meta"], self.cfg["geo"]
        d = _haversine_km(lead.get("lat"), lead.get("lng"), m["base_lat"], m["base_lng"])
        if d is None:
            return 0, None
        if d <= m["max_service_radius_km"]:
            return g["in_radius_bonus"], f"{d:.0f}km away (+{g['in_radius_bonus']})"
        return g["out_of_radius_penalty"], f"{d:.0f}km away ({g['out_of_radius_penalty']})"

    # -- اصلی ------------------------------------------------------------------------
    def score(self, lead: dict) -> ScoredLead:
        hay = _haystack(lead)
        reasons: list[str] = []

        skip_reason = self._hard_skip(hay, lead)
        if skip_reason:
            return ScoredLead("filtered", "Hard filter", 0, "skip", [skip_reason], lead)

        cat_name, cat = self._route(hay)
        total = cat.get("base", 0)
        reasons.append(f"{cat.get('label', cat_name)} (base {cat.get('base', 0)})")

        for sig_name, sig in self.cfg["signals"].items():
            hits = _matches(hay, sig.get("any_phrase"))
            if hits:
                total += sig["weight"]
                sign = "+" if sig["weight"] >= 0 else ""
                reasons.append(f"{sig_name}: {', '.join(hits[:3])} ({sign}{sig['weight']})")

        vb, vr = self._value_bonus(lead)
        total += vb
        if vr:
            reasons.append(vr)
        elif lead.get("cost_of_development") is None:
            reasons.append("value unknown (no bonus)")

        gb, gr = self._geo_adjust(lead)
        total += gb
        if gr:
            reasons.append(gr)

        score = max(0, min(100, total))

        a = self.cfg["actions"]
        if score >= a["draft_threshold"]:
            action = "draft"
        elif score >= a["save_threshold"]:
            action = "save"
        else:
            action = "skip"

        return ScoredLead(cat_name, cat.get("label", cat_name), score, action, reasons, lead)


def score_lead(lead: dict) -> ScoredLead:
    """میان‌بُرِ ماژول‌سطح — امتیازدهیِ یک لید با کانفیگِ پیش‌فرض."""
    return LeadScorer().score(lead)
