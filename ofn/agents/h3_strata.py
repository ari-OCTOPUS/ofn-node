"""H3 NSW Strata Hub adapter — read-only, stdlib only, collection-only.

Pulls strata plan records from the NSW Strata Hub FeatureServer (ArcGIS
REST, public, no auth) and maps them to normalized property-lead records.

Source (verified live, no auth):
  https://portal.spatial.nsw.gov.au/server/rest/services/StrataHub/FeatureServer/0/query

Design (matches h1_buysw pattern):
  * parse_feature()      — one ArcGIS feature -> normalized dict (pure)
  * classify_area()      — geo tier from LGA (pure, deterministic)
  * build_records()      — list of features -> list of records (pure)
  * fetch_page()         — injectable HTTP (the only I/O); default uses urllib
  * harvest()            — orchestration; fetch is a parameter for testability

COLLECTION-ONLY: this module never sends anything. It produces records for
the CRM/dedup layer. No outbox, no email, no external effect beyond the GET.

Owner decisions encoded (2026-09-02):
  * Service area = Sydney + ~100km, but leads OUTSIDE it are KEPT and flagged
    'out_of_area' for referral/resale — never rejected on distance alone.
  * No minimum-lots filter. lots recorded if present, empty if absent, never
    guessed.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Optional

TENANT = "lead"
SOURCE_ID = "nsw_strata_hub"

FEATURESERVER_URL = (
    "https://portal.spatial.nsw.gov.au/server/rest/services"
    "/StrataHub/FeatureServer/0/query"
)

# Fields we request from the FeatureServer (verified to exist in layer schema).
OUT_FIELDS = "plannumber,registrationdate,address,suburb,lga,lottotal,postcode"

# --- Service area (owner decision: Sydney + ~100km) --------------------------
# Derived from the live LGA list (123 LGAs, 88,881 strata plans). LGA names are
# stored UPPERCASE in the source; we compare uppercased.

# Tier 1 — Sydney metro core (~0-50km)
TIER1_METRO = frozenset({
    "SYDNEY", "NORTH SYDNEY", "RANDWICK", "WAVERLEY", "WOOLLAHRA",
    "BAYSIDE", "INNER WEST", "CANADA BAY", "CANTERBURY-BANKSTOWN",
    "GEORGES RIVER", "SUTHERLAND SHIRE", "NORTHERN BEACHES", "MOSMAN",
    "WILLOUGHBY", "LANE COVE", "HUNTERS HILL", "RYDE", "CITY OF PARRAMATTA",
    "CUMBERLAND", "STRATHFIELD", "BURWOOD", "KU-RING-GAI", "HORNSBY",
    "THE HILLS SHIRE", "BLACKTOWN", "FAIRFIELD", "LIVERPOOL",
    "CAMPBELLTOWN", "CAMDEN", "PENRITH",
})

# Tier 2 — Greater Sydney + ~100km ring
TIER2_GREATER = frozenset({
    "CENTRAL COAST", "WOLLONGONG", "SHELLHARBOUR", "BLUE MOUNTAINS",
    "HAWKESBURY", "WOLLONDILLY", "WINGECARRIBEE", "KIAMA",
    "LAKE MACQUARIE", "NEWCASTLE", "MAITLAND", "CESSNOCK", "PORT STEPHENS",
})


def classify_area(lga: Optional[str]) -> str:
    """Deterministic geo tier from LGA name.

    Returns one of: 'tier1_metro', 'tier2_greater', 'out_of_area', 'unknown'.
    'out_of_area' is a KEEP-and-flag verdict (referral/resale), not a reject.
    """
    if not lga:
        return "unknown"
    key = lga.strip().upper()
    if key in TIER1_METRO:
        return "tier1_metro"
    if key in TIER2_GREATER:
        return "tier2_greater"
    return "out_of_area"


def _epoch_ms_to_year(ts: object) -> Optional[int]:
    """Convert ArcGIS epoch-milliseconds (may be negative) to a 4-digit year.

    Returns None if ts is missing or not an int. Never guesses.
    """
    if not isinstance(ts, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).year
    except (OverflowError, OSError, ValueError):
        return None


def parse_feature(feature: dict) -> Optional[dict]:
    """Extract normalized fields from one ArcGIS feature.

    Returns a normalized record dict, or None if the essential id
    (plannumber) is missing. Never fabricates: absent fields stay empty/None.
    """
    attrs = feature.get("attributes") or {}
    plan = attrs.get("plannumber")
    if plan is None:
        return None

    lga = attrs.get("lga")
    reg_year = _epoch_ms_to_year(attrs.get("registrationdate"))
    lots = attrs.get("lottotal")  # may be None; keep as-is, never guess

    # Deterministic id from plan number.
    plan_str = str(plan)
    tender_id = f"{TENANT}:strata:{plan_str}"

    return {
        "tenant_id": TENANT,
        "tender_id": tender_id,
        "plan_number": plan,
        "plan_label": f"SP{plan}",
        "title": f"Strata scheme SP{plan}"
                 + (f" — {attrs.get('address')}" if attrs.get("address") else ""),
        "address": attrs.get("address") or "",
        "suburb": attrs.get("suburb") or "",
        "lga": lga or "",
        "postcode": attrs.get("postcode"),
        "lots": lots,  # None if absent — not guessed
        "registration_year": reg_year,  # None if absent
        "area_tier": classify_area(lga),
        "source": SOURCE_ID,
        "source_url": (
            "https://portal.spatial.nsw.gov.au/server/rest/services"
            f"/StrataHub/FeatureServer/0/query?where=plannumber%3D{plan_str}&f=json"
        ),
        "access_mode": "official_api",
        "evidence_status": "unverified",
        "status": "received",
        "segment": "strata",
    }


def build_records(features: list) -> list:
    """Map a list of ArcGIS features to normalized records.

    Drops features with no plannumber (parse_feature -> None). Keeps
    everything else, including out-of-area (flagged, not rejected).
    """
    out = []
    for f in features:
        rec = parse_feature(f)
        if rec is not None:
            out.append(rec)
    return out


# --- I/O layer (injectable) --------------------------------------------------
# The ONLY network access in this module. harvest() takes fetch as a parameter
# so tests run fully offline.

def fetch_page(
    where: str = "1=1",
    result_offset: int = 0,
    result_record_count: int = 2000,
    *,
    timeout: int = 30,
    base_url: str = FEATURESERVER_URL,
    out_fields: str = OUT_FIELDS,
) -> dict:
    """Fetch one page from the Strata Hub FeatureServer. Returns parsed JSON.

    per-host concurrency 1 is the caller's responsibility (harvest is serial).
    Geometry is not requested (returnGeometry=false) — we only need attributes.
    """
    params = {
        "where": where,
        "outFields": out_fields,
        "resultOffset": str(result_offset),
        "resultRecordCount": str(result_record_count),
        "returnGeometry": "false",
        "orderByFields": "plannumber",
        "f": "json",
    }
    url = base_url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "User-Agent": "octopus-lead-harvester/1.0 (strata-hub; public data)",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def harvest(
    where: str = "1=1",
    *,
    fetch: Callable[..., dict] = fetch_page,
    page_size: int = 2000,
    max_pages: int = 50,
) -> list:
    """Collect normalized strata records, paginating until exhausted.

    fetch is injected (default: real HTTP). Serial pagination = per-host
    concurrency 1. Stops when a page returns fewer than page_size features,
    or max_pages is hit (safety cap).

    COLLECTION-ONLY: returns records. Does not write, score, or send.
    """
    records: list = []
    offset = 0
    for _ in range(max_pages):
        page = fetch(
            where=where,
            result_offset=offset,
            result_record_count=page_size,
        )
        features = page.get("features") or []
        records.extend(build_records(features))
        if len(features) < page_size:
            break  # last page
        offset += page_size
    return records
