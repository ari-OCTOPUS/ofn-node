#!/usr/bin/env python3
"""pricing.py — تخمینِ قیمتِ نقاشی سیدنی (CONFIG-driven، propose-only).

منبع: hipages, LocalAgentFinder, Service.com.au, Painters Institute, QuoteYard (2025-2026).
هیچ عدد قطعی — همیشه بازهٔ (lo, hi). پولِ واقعی = تصمیمِ مالک.

NSW Home Building Act §8: بیعانهٔ نهایتاً ۱۰٪ از مبلغِ قرارداد.
ATO: GST 10% روی تمام sales > AUD 82.50.

$0 · stdlib + opslib · fail-soft.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_OPS = _HERE.parent
if str(_OPS / "budget") not in sys.path:
    sys.path.insert(0, str(_OPS / "budget"))
import opslib  # noqa: E402

# ─── Research-backed rate ranges (AUD/m², Sydney 2025-2026) ─────────────────────
# Source: hipages, LocalAgentFinder, service.com.au, painters.edu.au, thequoteyard.com.au
# These are CONFIG-overridable; hardcodes are fallback only.

# rate per m²: (lo, hi) — EXCL. paint materials (labor-only base)
LABOR_RATES: dict[str, dict[str, dict[str, tuple[float, float]]]] = {
    "interior": {
        "standard": {"wall": (18.0, 30.0), "ceiling": (20.0, 35.0), "trim": (25.0, 45.0)},
        "premium":  {"wall": (30.0, 45.0), "ceiling": (35.0, 50.0), "trim": (40.0, 60.0)},
        "trade":    {"wall": (15.0, 22.0), "ceiling": (18.0, 28.0), "trim": (20.0, 35.0)},
    },
    "exterior": {
        "standard": {"wall": (22.0, 40.0), "trim": (28.0, 50.0), "fascia": (25.0, 45.0)},
        "premium":  {"wall": (40.0, 65.0), "trim": (45.0, 70.0), "fascia": (40.0, 60.0)},
        "trade":    {"wall": (18.0, 30.0), "trim": (22.0, 38.0), "fascia": (20.0, 32.0)},
    },
}

# Multipliers for factors that shift the base rate
PREP_FACTORS: dict[str, tuple[float, float]] = {
    "minimal":  (0.80, 0.90),   # light sand, clean surface
    "standard":  (1.00, 1.00),   # normal prep (sand + fill + prime)
    "heavy":     (1.20, 1.40),   # extensive sanding, stripping, major repairs
}

ACCESS_FACTORS: dict[str, tuple[float, float]] = {
    "ladder":      (1.00, 1.00),
    "scaffold":    (1.10, 1.20),
    "swing_stage": (1.15, 1.30),
}

RISK_FACTOR = (1.10, 1.25)  # lead_paint, asbestos, heritage → +10-25%

# Segment influence on pricing (some segments command premium)
SEGMENT_MARKUP: dict[str, tuple[float, float]] = {
    "residential": (1.00, 1.00),
    "strata":      (1.05, 1.15),  # formal/committee overhead
    "pm":          (0.95, 1.05),  # property manager: fast, competitive
    "builder":     (0.90, 1.00),  # sub-contract: rate-card driven
    "commercial":  (1.10, 1.25),  # compliance, OH&S, staging
}

# Coat multiplier (base assumes 2 coats: 1 undercoat + 1 finish)
COAT_MULTIPLIER: dict[int, tuple[float, float]] = {
    1: (0.55, 0.70),
    2: (1.00, 1.00),   # baseline
    3: (1.40, 1.55),
}

# Material estimate: paint cost per m² (including rollers, tape, drop sheets)
MATERIAL_PER_M2: tuple[float, float] = (5.0, 12.0)  # AUD/m²

# GST
GST_RATE = 0.10  # 10% ATO standard

# NSW deposit cap (Home Building Act §8)
NSW_DEPOSIT_CAP_PCT = 0.10


@dataclass(frozen=True)
class QuoteIntake:
    """ساختاریافته‌ترین intake برای تخمینِ قیمت.
    همه فیلدها optional با fallback — سازگار با عقب: scope ساده هم پذیرفته می‌شود."""
    scope: str = ""
    size_m2: float = 0.0
    area_type: str = "interior"          # "interior" | "exterior" | "both"
    surface_type: str = "wall"            # "wall" | "ceiling" | "trim" | "fascia"
    surface_condition: str = "good"       # "good" | "fair" | "poor"
    prep_level: str = "standard"         # "minimal" | "standard" | "heavy"
    access_type: str = "ladder"          # "ladder" | "scaffold" | "swing_stage"
    segment: str = "residential"         # "residential" | "strata" | "pm" | "builder" | "commercial"
    paint_quality: str = "standard"      # "standard" | "premium" | "trade"
    coat_count: int = 2                  # 1, 2, 3
    risk_flags: tuple[str, ...] = ()     # ("lead_paint", "asbestos", "heritage")
    rooms: tuple[str, ...] = ()          # optional: ("kitchen", "bedroom-1", ...)
    timeline: str = "flexible"          # "asap" | "flexible" | "fixed_date"

    def __post_init__(self):
        # validate enum-like fields — fail-soft: bad values → default
        for attr, valid, default in [
            ("area_type", ("interior", "exterior", "both"), "interior"),
            ("surface_type", ("wall", "ceiling", "trim", "fascia"), "wall"),
            ("surface_condition", ("good", "fair", "poor"), "good"),
            ("prep_level", ("minimal", "standard", "heavy"), "standard"),
            ("access_type", ("ladder", "scaffold", "swing_stage"), "ladder"),
            ("segment", ("residential", "strata", "pm", "builder", "commercial"), "residential"),
            ("paint_quality", ("standard", "premium", "trade"), "standard"),
            ("timeline", ("asap", "flexible", "fixed_date"), "flexible"),
        ]:
            val = getattr(self, attr)
            if val not in valid:
                object.__setattr__(self, attr, default)

    def to_dict(self) -> dict:
        return {
            "scope": self.scope,
            "size_m2": self.size_m2,
            "area_type": self.area_type,
            "surface_type": self.surface_type,
            "surface_condition": self.surface_condition,
            "prep_level": self.prep_level,
            "access_type": self.access_type,
            "segment": self.segment,
            "paint_quality": self.paint_quality,
            "coat_count": self.coat_count,
            "risk_flags": list(self.risk_flags),
            "rooms": list(self.rooms),
            "timeline": self.timeline,
        }


@dataclass
class LineItem:
    """یک ردیفِ کوت: توضیح + کمیت + واحد + نرخ + جمع."""
    description: str
    qty: float
    unit: str           # "m2", "room", "lot", "day"
    rate_lo: float
    rate_hi: float
    subtotal_lo: float = 0.0
    subtotal_hi: float = 0.0

    def __post_init__(self):
        self.subtotal_lo = round(self.qty * self.rate_lo, 2)
        self.subtotal_hi = round(self.qty * self.rate_hi, 2)

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "qty": self.qty,
            "unit": self.unit,
            "rate_aud": [self.rate_lo, self.rate_hi],
            "subtotal_aud": [self.subtotal_lo, self.subtotal_hi],
        }


@dataclass
class PriceBreakdown:
    """خروجیِ کاملِ تخمینِ قیمت."""
    line_items: list[LineItem] = field(default_factory=list)
    labor_lo: float = 0.0
    labor_hi: float = 0.0
    material_lo: float = 0.0
    material_hi: float = 0.0
    subtotal_lo: float = 0.0    # excl GST
    subtotal_hi: float = 0.0
    gst_lo: float = 0.0
    gst_hi: float = 0.0
    total_lo: float = 0.0       # incl GST
    total_hi: float = 0.0
    max_deposit: float = 0.0   # 10% of mid-total (NSW cap)
    assumptions_auto: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "line_items": [li.to_dict() for li in self.line_items],
            "labor_aud": [self.labor_lo, self.labor_hi],
            "material_aud": [self.material_lo, self.material_hi],
            "subtotal_excl_gst": [self.subtotal_lo, self.subtotal_hi],
            "gst": [self.gst_lo, self.gst_hi],
            "total_incl_gst": [self.total_lo, self.total_hi],
            "max_deposit_nsw": self.max_deposit,
            "assumptions": self.assumptions_auto,
        }


def _rate_for(intake: QuoteIntake) -> tuple[float, float]:
    """نرخِ پایهٔ labor per m² از جدول."""
    area = intake.area_type
    if area == "both":
        # average of interior + exterior wall rates
        inner = LABOR_RATES.get("interior", {}).get(intake.paint_quality, {}).get("wall", (20.0, 30.0))
        outer = LABOR_RATES.get("exterior", {}).get(intake.paint_quality, {}).get("wall", (25.0, 40.0))
        return ((inner[0] + outer[0]) / 2, (inner[1] + outer[1]) / 2)
    surface = intake.surface_type
    rates = LABOR_RATES.get(area, {}).get(intake.paint_quality, {})
    return rates.get(surface, rates.get("wall", (20.0, 35.0)))


def estimate_price(intake: QuoteIntake) -> PriceBreakdown:
    """تخمینِ قیمت از intake. خروجی: بازهٔ (lo, hi) — هرگز عدد قطعی.
    propose-only: فقط draft — قیمت واقعی = تصمیم مالک."""
    result = PriceBreakdown()
    m2 = max(float(intake.size_m2), 0.0)

    # ── labor ────────────────────────────────────────────────────────────────
    if m2 > 0:
        base_lo, base_hi = _rate_for(intake)

        # prep factor
        pf = PREP_FACTORS.get(intake.prep_level, (1.0, 1.0))
        base_lo *= pf[0]; base_hi *= pf[1]

        # access factor
        af = ACCESS_FACTORS.get(intake.access_type, (1.0, 1.0))
        base_lo *= af[0]; base_hi *= af[1]

        # coat multiplier
        cm = COAT_MULTIPLIER.get(intake.coat_count, (1.0, 1.0))
        base_lo *= cm[0]; base_hi *= cm[1]

        # segment markup
        sm = SEGMENT_MARKUP.get(intake.segment, (1.0, 1.0))
        base_lo *= sm[0]; base_hi *= sm[1]

        # surface condition (fair=+5-10%, poor=+15-25%)
        cond_mult = {"good": (1.0, 1.0), "fair": (1.05, 1.10), "poor": (1.15, 1.25)}
        cf = cond_mult.get(intake.surface_condition, (1.0, 1.0))
        base_lo *= cf[0]; base_hi *= cf[1]

        # risk
        if intake.risk_flags:
            base_lo *= RISK_FACTOR[0]; base_hi *= RISK_FACTOR[1]

        base_lo = round(base_lo, 2)
        base_hi = round(base_hi, 2)

        result.line_items.append(LineItem(
            description=f"Labor: {intake.area_type} {intake.surface_type} "
                        f"(prep: {intake.prep_level}, {intake.coat_count} coat(s))",
            qty=m2, unit="m2", rate_lo=base_lo, rate_hi=base_hi))

        result.labor_lo = round(m2 * base_lo, 2)
        result.labor_hi = round(m2 * base_hi, 2)

        # ── materials ───────────────────────────────────────────────────────
        mat_lo, mat_hi = MATERIAL_PER_M2
        # premium paint adds 30-50% material cost
        if intake.paint_quality == "premium":
            mat_lo *= 1.30; mat_hi *= 1.50
        mat_lo = round(mat_lo, 2); mat_hi = round(mat_hi, 2)

        result.line_items.append(LineItem(
            description=f"Materials: paint + supplies ({intake.paint_quality})",
            qty=m2, unit="m2", rate_lo=mat_lo, rate_hi=mat_hi))

        result.material_lo = round(m2 * mat_lo, 2)
        result.material_hi = round(m2 * mat_hi, 2)

    # ── totals ────────────────────────────────────────────────────────────────
    result.subtotal_lo = round(result.labor_lo + result.material_lo, 2)
    result.subtotal_hi = round(result.labor_hi + result.material_hi, 2)
    result.gst_lo = round(result.subtotal_lo * GST_RATE, 2)
    result.gst_hi = round(result.subtotal_hi * GST_RATE, 2)
    result.total_lo = round(result.subtotal_lo + result.gst_lo, 2)
    result.total_hi = round(result.subtotal_hi + result.gst_hi, 2)
    result.max_deposit = round((result.total_lo + result.total_hi) / 2 * NSW_DEPOSIT_CAP_PCT, 2)

    # ── auto-assumptions (OPS-01 §4) ────────────────────────────────────────
    result.assumptions_auto = _generate_assumptions(intake)

    return result


def _generate_assumptions(intake: QuoteIntake) -> list[str]:
    """فرضیاتِ خودکار بر اساس intake (OPS-01 §4)."""
    a = [
        "Standard residential painting conditions assumed",
        "Client to clear rooms of furniture / cover remaining items",
        "No structural repairs included",
        f"Surface condition assessed as: {intake.surface_condition}",
    ]
    if intake.prep_level == "standard":
        a.append("Standard prep: sanding, minor filling, spot priming")
    elif intake.prep_level == "heavy":
        a.append("Heavy prep: full sanding, extensive filling, full priming")
    else:
        a.append("Minimal prep: light sanding only (surface in good condition)")

    if intake.access_type == "scaffold":
        a.append("Scaffolding hire NOT included in this estimate")
    elif intake.access_type == "swing_stage":
        a.append("Swing stage hire NOT included in this estimate")

    if "lead_paint" in intake.risk_flags:
        a.append("⚠️ Lead paint suspected — licensed remediation required (NOT included)")
    if "asbestos" in intake.risk_flags:
        a.append("⚠️ Asbestos suspected — licensed removal required (NOT included)")
    if "heritage" in intake.risk_flags:
        a.append("⚠️ Heritage property — council approval may be required")

    a.append(f"Valid for 30 days from issue date")
    a.append(f"Maximum deposit: 10% (NSW Home Building Act §8)")
    return a


if __name__ == "__main__":
    import json
    intake = QuoteIntake(
        scope="Full interior repaint — 3 bedroom house",
        size_m2=120.0, area_type="interior", surface_type="wall",
        prep_level="standard", access_type="ladder", segment="residential",
        paint_quality="standard", coat_count=2,
    )
    bd = estimate_price(intake)
    print(json.dumps(bd.to_dict(), ensure_ascii=False, indent=2))
