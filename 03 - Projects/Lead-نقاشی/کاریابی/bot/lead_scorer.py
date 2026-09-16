#!/usr/bin/env python3
"""
score_lead.py — config-driven lead scorer + router for a painting operator.

Reads painter_lead_scoring.yaml and turns a raw lead (dict) into:
  - category   : which buyer type it belongs to
  - score      : 0-100
  - action     : "draft" | "save" | "skip"
  - reasons    : human-readable explanation (matched signals)
  - card       : a Telegram-style alert string ready for your bot

A lead dict can contain (all optional except description):
  {
    "description": "Change of use to retail premises, including internal fitout...",
    "address":     "106 King Street Sydney NSW 2000",
    "council":     "City of Sydney",
    "cost_of_development": 480000,    # None if unknown (PlanningAlerts has no cost)
    "lat": -33.8675, "lng": 151.2070,
    "applicant": "ACME Shopfitters Pty Ltd",
    "url": "https://...",
    "source": "planning_alerts",
  }

Dependencies: pyyaml (stdlib otherwise).
"""

from __future__ import annotations
import math
import yaml
from pathlib import Path
from dataclasses import dataclass, field

CONFIG_PATH = Path(__file__).with_name("painter_lead_scoring.yaml")


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _haystack(lead: dict) -> str:
    """Lowercased text we search keywords against."""
    parts = [str(lead.get("description", "")), str(lead.get("address", ""))]
    return " ".join(parts).lower()


def _matches(haystack: str, phrases) -> list[str]:
    """Return the phrases that appear as substrings in the haystack."""
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


# --------------------------------------------------------------------------- #
# result type
# --------------------------------------------------------------------------- #
@dataclass
class ScoredLead:
    category: str
    category_label: str
    score: int
    action: str
    reasons: list[str] = field(default_factory=list)
    lead: dict = field(default_factory=dict)

    def card(self) -> str:
        """Telegram-style alert that mirrors your existing bot output."""
        L = self.lead
        emoji = {"draft": "🟢", "save": "🟡", "skip": "⚪️"}.get(self.action, "🏢")
        lines = [
            f"{emoji} {L.get('source', 'planning_alerts')} | score: {self.score} | {self.category}",
            f"📌 {L.get('description', '').strip()}",
            f"📍 {L.get('address', 'n/a')}",
        ]
        if L.get("url"):
            lines.append(f"🔗 {L['url']}")
        lines.append("🧠 " + "; ".join(self.reasons))
        # action buttons reflect the recommendation by ordering it first
        order = {"draft": "/draft  /save  /skip",
                 "save":  "/save  /draft  /skip",
                 "skip":  "/skip  /save  /draft"}[self.action]
        lines.append(order)
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# the scorer
# --------------------------------------------------------------------------- #
class LeadScorer:
    def __init__(self, config: dict | None = None):
        self.cfg = config or _load_config()

    # -- hard filters -------------------------------------------------------- #
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

    # -- category routing ---------------------------------------------------- #
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

    # -- value + geo --------------------------------------------------------- #
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

    # -- main ---------------------------------------------------------------- #
    def score(self, lead: dict) -> ScoredLead:
        hay = _haystack(lead)
        reasons: list[str] = []

        skip_reason = self._hard_skip(hay, lead)
        if skip_reason:
            return ScoredLead("filtered", "Hard filter", 0, "skip",
                              [skip_reason], lead)

        cat_name, cat = self._route(hay)
        total = cat.get("base", 0)
        reasons.append(f"{cat.get('label', cat_name)} (base {cat.get('base', 0)})")

        # additive signals
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


# --------------------------------------------------------------------------- #
# demo
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    scorer = LeadScorer()

    samples = [
        {   # your real lead — commercial fitout, NOT strata
            "source": "planning_alerts",
            "description": ("Change of use to a retail premises, including internal "
                            "fitout, external facade works, lighting and business "
                            "identification signage."),
            "address": "106 King Street Sydney NSW 2000",
            "council": "City of Sydney",
            "cost_of_development": None,
            "lat": -33.8675, "lng": 151.2070,
            "url": "https://eplanning.cityofsydney.nsw.gov.au/...id=2684624",
        },
        {   # the dream lead — strata remedial repaint
            "source": "planning_alerts",
            "description": ("Remedial works to common property including rendering and "
                            "repainting of external facade and balcony balustrade "
                            "replacement to residential flat building of 24 units."),
            "address": "12 Wattle Crescent, Pyrmont NSW 2009",
            "council": "City of Sydney",
            "cost_of_development": 820000,
            "lat": -33.8700, "lng": 151.1950,
            "url": "https://example.com/da/strata",
        },
        {   # noise — should be filtered out
            "source": "planning_alerts",
            "description": "Demolition only of existing dwelling house.",
            "address": "5 Quiet St, Sydney NSW 2000",
            "cost_of_development": 60000,
            "lat": -33.87, "lng": 151.21,
        },
    ]

    for s in samples:
        print(scorer.score(s).card())
        print("-" * 70)
