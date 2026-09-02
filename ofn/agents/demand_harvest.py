"""DEAD SOURCE — labeled 2026-09-02 (D-31 step 1).

Both upstreams measured dead or empty on Day 7: the NSW eTendering OCDS
feed ENDED Feb 2025, and AusTender OCDS federal returned ~0 painting
awards (wrong backbone). Verified live from Sydney — see
docs/day7/DAY7-SOURCE-DISCOVERY-AND-OWNER-LOG.md and
docs/research/2026-09-02-demand-channels-deepdive.md. Do NOT wire new
callers to these sources. Disposition: repoint to live demand channels;
dead fetchers are removed at D-31 step 4.

---

Demand-side tender harvester — buyers of painting services (issue #55).

The first Seek harvest filled the lead table with job ADS: employers
looking to HIRE a painter (supply side), not customers looking to BUY
painting services (demand side). Sending a quote to an employer is
`wrong_recipient` — the PAINT-L5-001 kill metric.

This module harvests from sources where the counterpart BUYS painting
services: NSW eTendering OCDS and AusTender. Three gates locked in code:

  1. DIRECTION GATE — any supply-side signal (salary, employmentType,
     hiring verbs) is REJECTED before scoring. A permanent negative
     control pins this.
  2. 403 NEVER RETRIES — forbidden is a policy answer, not traffic.
     Only 429/5xx back off (exponentially, capped).
  3. NON-COMPENSATORY SCORE — geometric mean with a 1.5 ceiling;
     consent_ok=False or capacity_ok=False is a hard zero that no other
     dimension can outweigh.

Honest headers only (octopus-demand-harvester/1.0), ETag conditional
requests to minimise fetch volume, A0-A2 envelope (read-only, zero
external effect beyond the GET itself).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Callable, Mapping

USER_AGENT = "octopus-demand-harvester/1.0 (Ari; repo: ari-OCTOPUS/ofn-node)"
TIMEOUT_S = 20
MAX_RETRIES = 3
BACKOFF_BASE_S = 5
BACKOFF_MAX_S = 60

# ── Gate 1: supply-side rejection ────────────────────────────────────────

SUPPLY_KEYWORDS = frozenset({
    "salary", "per hour", "hourly rate", "wages", "award pay",
    "full-time", "part-time", "casual position", "we are hiring",
    "seeking a painter", "employment opportunity", "job opportunity",
    "apply now", "cv", "resume", "experience required", "abn holder wanted",
})

SUPPLY_EMPLOYMENT_TYPES = frozenset({
    "full_time", "part_time", "casual", "contract_equipment",
    "voluntary", "apprenticeship", "traineeship",
})


def is_supply_side(record: Mapping) -> bool:
    """True if ANY signal indicates the counterpart is hiring, not buying."""
    et = str(record.get("employmentType", "") or "").lower().strip()
    if et in SUPPLY_EMPLOYMENT_TYPES:
        return True
    text = " ".join([
        str(record.get("title", "") or ""),
        str(record.get("description", "") or ""),
    ]).lower()
    return any(kw in text for kw in SUPPLY_KEYWORDS)


# ── Gate 2: fetch with 403-as-policy ─────────────────────────────────────

class HarvestError(Exception):
    """Fetch failure — park the cycle, never crash the loop."""


def fetch_json(
    url: str,
    *,
    etag: str = "",
    now_epoch_s: Callable[[], int] = lambda: int(time.time()),
) -> tuple[str | None, str]:
    """One GET; returns (body, etag). 403 → immediate HarvestError.

    304 returns (None, etag) — caller treats as "no change, skip".
    429/5xx retry with exponential backoff up to MAX_RETRIES.
    """
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    if etag:
        headers["If-None-Match"] = etag
    last: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return (resp.read().decode("utf-8", "replace"),
                        resp.headers.get("ETag", ""))
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                raise HarvestError(
                    "403 forbidden: this feed requires authorised access "
                    "(get an API key or use the observatory gateway); "
                    "the harvester will not spoof a browser") from exc
            if exc.code == 304:
                return (None, etag)
            if exc.code in (429, 500, 502, 503, 504):
                last = exc
                time.sleep(min(BACKOFF_BASE_S * (2 ** attempt),
                               BACKOFF_MAX_S))
                continue
            raise HarvestError(f"HTTP {exc.code}: {url}") from exc
        except Exception as exc:                  # noqa: BLE001 — park
            last = exc
            time.sleep(min(BACKOFF_BASE_S * (2 ** attempt), BACKOFF_MAX_S))
    raise HarvestError(f"fetch failed after {MAX_RETRIES}: {last}")


# ── OCDS parser (NSW eTendering quirks) ─────────────────────────────────

def strip_leading_space(value: str) -> str:
    """NSW pads numeric-only string IDs with ONE leading space. Only that
    exact one-space prefix is stripped — a blind strip() would eat real
    leading whitespace in names/descriptions."""
    return value[1:] if value.startswith(" ") else value


def parse_ocds_release(release: Mapping) -> dict | None:
    """Normalize one OCDS release; None if essential fields are missing.

    NSW quirks: empty fields are OMITTED (not empty strings), so every
    .get() defaults to None; buyer.name may be non-string → None.
    """
    tender = release.get("tender") or {}
    buyer = release.get("buyer") or {}
    rftuuid = tender.get("RFTUUID")
    title = tender.get("title")
    if not rftuuid or not title:
        return None
    buyer_name = buyer.get("name")
    if not isinstance(buyer_name, str):
        buyer_name = None
    loc = (tender.get("deliveryLocation") or {})
    gaz = (loc.get("gazetteer") or {})
    regions = [strip_leading_space(str(r))
               for r in (gaz.get("Identifiers") or [])]
    val = tender.get("value") or {}
    amount = val.get("amount") if isinstance(val, dict) else None
    period = tender.get("tenderPeriod") or {}
    closing = period.get("endDate")
    items = tender.get("items") or []
    unspsc = [str(((it.get("classification") or {}).get("id") or ""))
              for it in items]
    return {
        "rftuuid": strip_leading_space(str(rftuuid)),
        "employmentType": str(tender.get("employmentType") or ""
                               ).lower().strip(),
        "title": str(title),
        "description": str(tender.get("description") or ""),
        "buyer_name": buyer_name,
        "regions": [r for r in regions if r],
        "amount": amount,
        "closing_at": str(closing) if closing else "",
        "unspsc_codes": [c for c in unspsc if c],
        "source_url": (f"https://tenders.nsw.gov.au/?event=public.api."
                       f"tender.view&RFTUUID={rftuuid}"),
    }


# ── Gate 3: non-compensatory score ───────────────────────────────────────

def score_demand(record: Mapping) -> dict:
    """Geometric-mean score, ceiling 1.5, hard-zero gates.

    consent_ok=False → 0.0 (no amount/buyer disclosure = no consent basis)
    capacity_ok=False → 0.0 (outside service area or below minimum value)
    Neither can be outweighed by any other dimension being high.
    """
    amount = record.get("amount")
    buyer = record.get("buyer_name")
    consent_ok = amount is not None and amount > 0 and bool(buyer)
    regions = record.get("regions") or []
    in_service_area = any(r in SERVICE_REGIONS for r in regions) if regions else False
    min_value_ok = amount is not None and amount >= MIN_VALUE_AUD
    capacity_ok = in_service_area and min_value_ok

    if not consent_ok or not capacity_ok:
        return {"score": 0.0, "recommendation": "reject",
                "consent_ok": consent_ok, "capacity_ok": capacity_ok,
                "reason": "hard-zero gate"}

    # painting relevance (keyword + UNSPSC)
    text = (str(record.get("title", "")) + " " +
            str(record.get("description", ""))).lower()
    kw_count = sum(1 for kw in PAINTING_KEYWORDS if kw in text)
    has_unspsc = any(c in PAINTING_UNSPSC
                     for c in record.get("unspsc_codes", []))
    p = min(1.0, 0.5 + 0.15 * kw_count + (0.3 if has_unspsc else 0.0))

    # geography
    g = min(1.0, sum(1 for r in regions if r in SERVICE_REGIONS)
            / max(len(regions), 1))

    # deadline
    closing = str(record.get("closing_at", ""))
    d = 0.3
    if closing:
        try:
            from datetime import datetime, timezone
            close_dt = datetime.fromisoformat(
                closing.replace("Z", "+00:00"))
            days = (close_dt - datetime.now(timezone.utc)).days
            d = (0.1 if days < 3 else 0.4 if days < 7
                 else 0.7 if days < 14 else 0.9)
        except (ValueError, TypeError):
            d = 0.3

    # evidence quality (official API = high)
    q = 0.7

    score = min(1.5, (p * g * d * q) ** 0.25)
    return {"score": round(score, 3),
            "recommendation": "bid" if score >= 0.8 else "watch",
            "consent_ok": consent_ok, "capacity_ok": capacity_ok,
            "reason": "geometric-mean"}


SERVICE_REGIONS = frozenset({
    "sydney", "cumberland/prospect", "nepean", "northern sydney",
    "inner west", "south east sydney", "south west sydney",
    "central coast", "illawarra", "hunter",
})

MIN_VALUE_AUD = 400

PAINTING_KEYWORDS = frozenset({
    "painting", "repaint", "repainting", "external painting",
    "internal painting", "coating", "facade repaint",
    "paint work", "paintwork",
})

PAINTING_UNSPSC = frozenset({
    "72151300", "72151301", "72151302",
})


# Legacy NSW eTendering search. Host redirects to buy.nsw.gov.au; this
# event URL is dead. Do not invent a buy.nsw API. In-tree alternative:
# nsw_ocp_harvest.py.
NSW_ETENDERING_SEARCH_URL = (
    "https://tenders.nsw.gov.au/?event=public.api.tender.search"
)
NSW_ETENDERING_FEED_STATUS = "dead_redirect_buy_nsw"


# ── cycle ─────────────────────────────────────────────────────────────────

def cycle(
    fetch: Callable[..., tuple],
    existing_ids: Callable[[], set],
    create_lead: Callable[[Mapping], dict],
    notify: Callable[[str, str, Mapping], bool] | None = None,
    *,
    url: str = NSW_ETENDERING_SEARCH_URL,
    etag: str = "",
) -> dict:
    """One harvest cycle. Returns accounting; parks on feed failure."""
    try:
        body, new_etag = fetch(url, etag=etag)
    except HarvestError as exc:
        return {"status": "PARKED", "reason": str(exc)[:200],
                "candidates": 0, "new": 0, "notified": 0, "etag": etag}
    if body is None:
        return {"status": "NO_CHANGE", "candidates": 0, "new": 0,
                "notified": 0, "etag": new_etag}
    try:
        releases = json.loads(body)
        if isinstance(releases, dict):
            releases = releases.get("releases", [])
    except (json.JSONDecodeError, AttributeError):
        return {"status": "PARKED", "reason": "feed is not valid JSON",
                "candidates": 0, "new": 0, "notified": 0, "etag": etag}

    seen = existing_ids()
    created, notified, rejected = 0, 0, 0
    for release in releases:
        parsed = parse_ocds_release(release)
        if parsed is None:
            continue
        if is_supply_side(parsed):
            rejected += 1
            continue
        score = score_demand(parsed)
        if score["score"] == 0.0:
            rejected += 1
            continue
        lead_id = f"nsw_tender:{parsed['rftuuid']}"
        if lead_id in seen:
            continue
        lead = {
            "lead_id": lead_id,
            "channel": "nsw_tender",
            "name": parsed["title"][:200],
            "suburb": ", ".join(parsed["regions"])[:120],
            "source_url": parsed["source_url"],
            "status": "new",
            "notes": (f"Buyer: {parsed['buyer_name']} | Value: "
                      f"${parsed['amount']} | Score: {score['score']} | "
                      f"Rec: {score['recommendation']}"),
        }
        result = create_lead(lead)
        if result.get("ok"):
            created += 1
            seen.add(lead_id)
            if notify is not None:
                try:
                    notify(lead_id, "DEMAND_LEAD_FOUND", {
                        "title": parsed["title"][:80],
                        "buyer": parsed["buyer_name"],
                        "score": score["score"],
                    })
                    notified += 1
                except Exception:            # noqa: BLE001
                    pass
    return {"status": "DONE", "candidates": len(releases),
            "rejected_supply": rejected, "new": created,
            "notified": notified, "etag": new_etag}
