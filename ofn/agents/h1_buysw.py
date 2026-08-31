"""H1 buy.nsw tender adapter — read-only, stdlib only.

Parses NSW eTendering OCDS responses, filters for painting tenders
in Sydney service area, maps to painting_tenders schema.
"""
import json
import urllib.request
from datetime import datetime, timezone

TENANT = "lead"
SOURCE_ID = "buy_nsw_etendering"
MIN_VALUE_AUD = 400

# Sydney + ~100km service area (from OCDS xNSWRegions scheme)
ACCEPT_REGIONS = frozenset({
    "sydney", "cumberland/prospect", "nepean", "northern sydney",
    "inner west", "south east sydney", "south west sydney",
    "central coast", "illawarra", "hunter",
})

# Painting SERVICE keywords (case-insensitive, checked in title + description)
ACCEPT_KEYWORDS = frozenset({
    "painting", "repaint", "repainting", "external painting",
    "internal painting", "coating", "facade repaint",
    "paint work", "paintwork",
})

# REJECT: paint as product/supply/art, not service
REJECT_KEYWORDS = frozenset({
    "paint supply", "paint product", "art gallery", "exhibition",
    "artwork", "art collection", "painting exhibition",
    "paints and primers", "bulk paint",
})

# UNSPSC codes that mean painting SERVICE
ACCEPT_UNSPSC = frozenset({
    "72151300",  # Painting and paper hanging services
    "72151301",  # Residential painting service
    "72151302",  # Commercial painting service
})

# UNSPSC codes that mean paint PRODUCT (not service)
REJECT_UNSPSC = frozenset({
    "31211500",  # Paints and primers
    "31211501",  # Enamel paints
    "31211502",  # Water based paints
})


def parse_tender(release: dict) -> dict | None:
    """Extract normalized fields from one OCDS release.
    Returns dict or None if essential fields missing."""
    tender = release.get("tender", {})
    buyer = release.get("buyer", {})

    rftuuid = tender.get("RFTUUID")
    title = tender.get("title")
    if not rftuuid or not title:
        return None

    # location
    loc = tender.get("deliveryLocation", {})
    gaz = loc.get("gazetteer", {})
    regions = gaz.get("Identifiers", [])

    # value
    val_obj = tender.get("value", {})
    amount = val_obj.get("amount") if isinstance(val_obj, dict) else None

    # UNSPSC
    items = tender.get("items", [])
    unspsc_codes = []
    for item in items:
        cls = item.get("classification", {})
        code = cls.get("id", "")
        if code:
            unspsc_codes.append(code)

    # closing date
    period = tender.get("tenderPeriod", {})
    closing_at = period.get("endDate", "")

    return {
        "tender_id": f"{TENANT}:tender:buysw:{rftuuid}",
        "title": title,
        "description": tender.get("description", ""),
        "buyer_name": buyer.get("name", ""),
        "location": ", ".join(regions) if regions else "",
        "regions": [r.lower() for r in regions],
        "closing_at": closing_at,
        "amount": amount,
        "unspsc_codes": unspsc_codes,
        "source": SOURCE_ID,
        "source_url": f"https://tenders.nsw.gov.au/?event=public.api.tender.view&RFTUUID={rftuuid}",
        "access_mode": "official_api",
        "evidence_status": "unverified",
        "status": "received",
        "rftuuid": rftuuid,
        "e_tender_status": tender.get("eTenderStatus", ""),
    }


def filter_painting_tender(parsed: dict) -> bool:
    """Deterministic filter: keyword + location + min value + UNSPSC.
    Returns True if tender should be kept."""

    # --- UNSPSC reject (product, not service) ---
    for code in parsed.get("unspsc_codes", []):
        if code in REJECT_UNSPSC:
            return False

    # --- keyword check (title + description) ---
    text = (parsed.get("title", "") + " " + parsed.get("description", "")).lower()

    for rk in REJECT_KEYWORDS:
        if rk in text:
            return False

    has_painting_keyword = any(ak in text for ak in ACCEPT_KEYWORDS)
    has_painting_unspsc = any(c in ACCEPT_UNSPSC for c in parsed.get("unspsc_codes", []))

    if not has_painting_keyword and not has_painting_unspsc:
        return False

    # --- location: must overlap with service area ---
    regions = parsed.get("regions", [])
    if regions and not any(r in ACCEPT_REGIONS for r in regions):
        return False

    # --- minimum value ---
    amount = parsed.get("amount")
    if amount is not None and amount < MIN_VALUE_AUD:
        return False

    return True


def build_score_inputs(parsed: dict) -> dict:
    """Map parsed tender fields to tender_score P/G/E/D/M/Q/R/C inputs.
    All values 0.0-1.0. Conservative defaults for unknowns."""

    # P — painting relevance
    text = (parsed.get("title", "") + " " + parsed.get("description", "")).lower()
    has_unspsc = any(c in ACCEPT_UNSPSC for c in parsed.get("unspsc_codes", []))
    kw_count = sum(1 for ak in ACCEPT_KEYWORDS if ak in text)
    p = min(1.0, 0.5 + 0.15 * kw_count + (0.3 if has_unspsc else 0.0))

    # G — geography fit
    regions = parsed.get("regions", [])
    if not regions:
        g = 0.3  # unknown
    else:
        sydney_match = sum(1 for r in regions if r in ACCEPT_REGIONS)
        g = min(1.0, sydney_match / max(len(regions), 1))

    # E — eligibility fit (conservative: we don't know yet)
    e = 0.5

    # D — deadline feasibility
    closing = parsed.get("closing_at", "")
    if closing:
        try:
            close_dt = datetime.fromisoformat(closing.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            days_left = (close_dt - now).days
            if days_left < 3:
                d = 0.1
            elif days_left < 7:
                d = 0.4
            elif days_left < 14:
                d = 0.7
            else:
                d = 0.9
        except (ValueError, TypeError):
            d = 0.3
    else:
        d = 0.3

    # M — margin confidence (unknown from API)
    m = 0.4

    # Q — evidence quality (API = official source)
    q = 0.7

    # R — policy risk (conservative default)
    r = 0.3

    # C — bid cost (unknown)
    c = 0.3

    return {"P": p, "G": g, "E": e, "D": d, "M": m, "Q": q, "R": r, "C": c}
