"""catalog_loader.py — پلِ کاتالوگِ عکس‌محور (ziman-catalog.json) به product_card.v1.

منبعِ حقیقت: 03-Offering/ziman-catalog.json — ۳۶ رکورد (۳۵ محصولِ گراندشده با
عکس + ۱ blank). هر رکورد به یک ProductCard با طرحِ ZIM-Fx-NN نگاشت می‌شود.

قواعدِ propose-only (هرگز نقض نمی‌شوند):
  • قیمت null و price_status="unknown" — جعلِ قیمت ممنوع (منتظرِ COGS/ZIM-V5).
  • موجودی null و evidence_class="UNKNOWN" — فقط ورودیِ مالک اعداد را پُر می‌کند.
  • F4 (همپرِ ترکیبی) و هر رکوردِ perishable → تحویلِ محلی (local_only)، fail-closed
    طبقِ R0-F1؛ چون ممکن است خوراکی داشته باشد.

stdlib-only · نسبت به فایلِ کاتالوگ فقط-خواندنی · هیچ اکشنِ بیرونی ندارد.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:  # داخلِ بستهٔ ziman
    from .product import (
        ALL_FAMILIES,
        CommercialBlock,
        InventoryBlock,
        ProductCard,
        ZIM_FAMILY_NAMES,
        _ZIM_PERISHABLE_FAMILIES,
    )
except ImportError:  # اجرای تخت (تست‌ها ziman/ را روی sys.path می‌گذارند)
    from product import (  # type: ignore
        ALL_FAMILIES,
        CommercialBlock,
        InventoryBlock,
        ProductCard,
        ZIM_FAMILY_NAMES,
        _ZIM_PERISHABLE_FAMILIES,
    )

_LONG_TO_SHORT = {v: k for k, v in ZIM_FAMILY_NAMES.items()}
_ALCOHOL_HINTS = ("alcohol", "wine", "champagne", "prosecco", "whisky",
                  "whiskey", "liqueur", "vodka", "gin", "sparkling")
_MAX_PERISHABLE_LEAD_DAYS = 3


# ── mapping helpers ─────────────────────────────────────────────────────────

def _short_family(family: str) -> str:
    """«F4_mixed_hamper» → «F4»؛ «OTHER» → «OTHER»؛ ناشناخته → «OTHER»."""
    if family in _LONG_TO_SHORT:
        return _LONG_TO_SHORT[family]
    if family in ZIM_FAMILY_NAMES:   # از قبل کوتاه بود
        return family
    return "OTHER"


def _has_alcohol(rec: dict[str, Any]) -> bool:
    hay = " ".join([
        str(rec.get("one_line", "")),
        str(rec.get("edible", "")),
        " ".join(rec.get("medium", []) or []),
    ]).lower()
    return any(h in hay for h in _ALCOHOL_HINTS)


def _personalisable(rec: dict[str, Any]) -> bool:
    p = (rec.get("personalisation") or "").strip().lower()
    return p not in ("", "none", "no", "n/a")


def card_from_record(rec: dict[str, Any]) -> ProductCard:
    """یک رکوردِ کاتالوگ → ProductCard (بدونِ قیمت/موجودیِ جعلی)."""
    short = _short_family(rec.get("family", "OTHER"))
    json_perishable = bool(rec.get("perishable"))
    # R0-F1: F4 همیشه محلی (fail-closed)، حتی اگر رکورد perishable را نگذاشته باشد.
    force_local = json_perishable or short in _ZIM_PERISHABLE_FAMILIES

    fulfilment: dict[str, Any] = {"delivery_promise_authority": False}
    if force_local:
        fulfilment["policy"] = "local_only"
        fulfilment["lead_time_days"] = _MAX_PERISHABLE_LEAD_DAYS
        if short in _ZIM_PERISHABLE_FAMILIES and not json_perishable:
            fulfilment["policy_reason"] = "R0-F1: F4 mixed hamper → local_only (fail-closed)"
    else:
        fulfilment["policy"] = "shippable"

    classification = {
        "family_name": ZIM_FAMILY_NAMES.get(short, "OTHER"),
        "form": rec.get("form", ""),
        "palette": rec.get("palette", ""),
        "edible": rec.get("edible", "none"),
        "perishable": json_perishable,          # صادقانه از شواهدِ عکس
        "alcohol": _has_alcohol(rec),           # facet — پخشِ الکل محدودیتِ سنی دارد
        "personalisable": _personalisable(rec),
        "occasion_fit": rec.get("occasion_fit", []) or [],
    }

    return ProductCard(
        product_id=rec["product_id"],
        family_id=short,
        title=(rec.get("one_line", "") or "")[:80],
        status="draft",
        classification=classification,
        inventory=InventoryBlock(),                     # همه null → UNKNOWN
        commercial=CommercialBlock(price_status="unknown"),  # قیمت null
        fulfilment=fulfilment,
        assets={
            "photo_files": rec.get("photo_files", []) or [],
            "photo_count": rec.get("photo_count", len(rec.get("photo_files", []) or [])),
        },
        evidence={
            "source": "03-Offering/ziman-catalog.json",
            "grounding": "photo_evidence",
            "truth_tier": "MEASURED(photo)+OWNER_INPUT",
        },
        governance={"propose_only": True, "price_status": "unknown"},
    )


# ── loading ─────────────────────────────────────────────────────────────────

def find_catalog_json(start: Path | None = None) -> Path | None:
    """کاتالوگ را با بالا رفتن از پوشهٔ جاری پیدا می‌کند (03-Offering/…)."""
    here = Path(start).resolve() if start else Path(__file__).resolve()
    for base in [here, *here.parents]:
        cand = base / "03-Offering" / "ziman-catalog.json"
        if cand.exists():
            return cand
    return None


def load_catalog(json_path: Path | str | None = None) -> list[ProductCard]:
    """کاتالوگ را می‌خواند و فقط کارت‌های معتبر (validate()==[]) را برمی‌گرداند.

    یک رکوردِ خرابِ منفرد نباید کلِ بارگذاری را بشکند (fail-safe).
    """
    path = Path(json_path) if json_path else find_catalog_json()
    if not path or not Path(path).exists():
        return []
    raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    cards: list[ProductCard] = []
    for rec in raw.get("products", []) or []:
        try:
            card = card_from_record(rec)
        except (KeyError, TypeError, ValueError):
            continue
        if card.validate() == []:
            cards.append(card)
    return cards


def catalog_summary(cards: list[ProductCard]) -> dict[str, Any]:
    """خلاصهٔ گراندشده برای گزارش/داشبورد — بدونِ اعدادِ جعلی."""
    by_family: dict[str, int] = {f: 0 for f in ALL_FAMILIES}
    perishable = local_only = priced = alcohol = 0
    for c in cards:
        by_family[c.family_id] = by_family.get(c.family_id, 0) + 1
        if c.classification.get("perishable"):
            perishable += 1
        if c.fulfilment.get("policy") == "local_only":
            local_only += 1
        if c.classification.get("alcohol"):
            alcohol += 1
        if c.commercial.public_price_aud is not None:
            priced += 1
    return {
        "total": len(cards),
        "by_family": {k: v for k, v in by_family.items() if v},
        "perishable": perishable,
        "local_only": local_only,
        "alcohol_facet": alcohol,
        "priced": priced,               # باید 0 بماند تا ZIM-V5
        "price_status": "all unknown (propose-only)",
    }
