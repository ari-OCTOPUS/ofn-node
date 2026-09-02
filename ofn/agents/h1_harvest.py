"""DEAD SOURCE — labeled 2026-09-02 (D-31 step 1).

Its only upstream, the NSW eTendering OCDS feed, ENDED Feb 2025 —
verified live from Sydney (docs/day7/DAY7-SOURCE-DISCOVERY-AND-OWNER-LOG.md).
A fetch loop over a dead feed cannot produce leads. Do NOT wire new
callers to it. Disposition: repoint the fetch layer to the sanctioned
channels (buy.nsw supplier-registration nightly email, info.buy.nsw
contract register) or remove at D-31 step 4.

---

H1 buy.nsw autonomous tender harvester — the missing fetch loop.

The h1_buysw agent (parse/filter/score) exists but nothing ever calls it:
no fetch, no dedup, no wiring into the node. This module is that loop.

Runs INSIDE the survival-loop's A0-A2 envelope (read-only public API,
fixture-tested scoring, zero external effect beyond a GET). Each cycle:

    1. GET the NSW eTendering OCDS feed (releases).
    2. parse_tender → filter_painting_tender → build_score_inputs.
    3. Skip tender_ids already in the store (idempotent).
    4. create_tender(...) — scored, unverified, no submit.
    5. Notify the owner queue (GREEN, cockpit-visible) for each NEW hit.

Network policy: single GET per cycle, stdlib only, timeout, one retry on
transient failure, park (not crash) on anything else — the survival-loop's
provider_outcome contract.
"""
from __future__ import annotations

import json
import time
import urllib.request
from typing import Callable, Mapping

from .h1_buysw import (
    SOURCE_ID, build_score_inputs, filter_painting_tender, parse_tender,
)

# NSW eTendering public OCDS feed (released tenders, most recent page).
FEED_URL = (
    "https://tenders.nsw.gov.au/?event=public.api.list"
    "&type=released&pagesize=100"
)
TIMEOUT_S = 20
MAX_RETRIES = 2


class TenderHarvestError(Exception):
    """Fetch/parse failure — park the cycle, never crash the loop."""


def fetch_releases(now_epoch_s: Callable[[], int]) -> list[dict]:
    """One GET; one retry on transient error; park otherwise."""
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                FEED_URL, headers={"Accept": "application/json",
                                   "User-Agent": "octopus-h1-tender/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            releases = body.get("releases", [])
            if not isinstance(releases, list):
                raise TenderHarvestError("feed shape unexpected: no list")
            return releases
        except Exception as exc:            # noqa: BLE001 — park, don't die
            last_exc = exc
            time.sleep(2 * (attempt + 1))
    raise TenderHarvestError(f"fetch failed after {MAX_RETRIES}: {last_exc}")


def harvest(releases: list[dict]) -> list[dict]:
    """Pure: OCDS releases → scored painting-tender payloads."""
    hits: list[dict] = []
    for release in releases:
        parsed = parse_tender(release)
        if parsed is None:
            continue
        if not filter_painting_tender(parsed):
            continue
        hits.append({
            "tender_id": f"{SOURCE_ID}:{parsed['rftuuid']}",
            "source": SOURCE_ID,
            "source_url": parsed.get("source_url", ""),
            "title": parsed["title"],
            "buyer_name": parsed.get("buyer_name", ""),
            "location": ", ".join(parsed.get("regions", [])),
            "closing_at": parsed.get("closing_at", ""),
            "score_inputs": build_score_inputs(parsed),
            "access_mode": "official_api",
            "evidence_status": "unverified",
            "status": "scored",
        })
    return hits


def cycle(
    store,                        # LeadStore-like (has .tenders())
    create_tender: Callable[[Mapping], dict],
    notify: Callable[[str, str, Mapping], bool] | None = None,
    *,
    now_epoch_s: Callable[[], int],
) -> dict:
    """One harvest cycle. Returns an accounting dict (no green theatre)."""
    try:
        releases = fetch_releases(now_epoch_s)
    except TenderHarvestError as exc:
        return {"status": "PARKED", "reason": str(exc)[:200],
                "fetched": 0, "candidates": 0, "new": 0, "notified": 0}

    hits = harvest(releases)
    existing = {t["tender_id"] for t in (store.tenders("lead", limit=500) or [])}
    created, notified = 0, 0
    for hit in hits:
        if hit["tender_id"] in existing:
            continue
        result = create_tender(hit)
        if result.get("ok"):
            created += 1
            existing.add(hit["tender_id"])
            if notify is not None:
                try:
                    notify(hit["tender_id"], "TENDER_FOUND", {
                        "title": hit["title"][:80],
                        "closing": hit.get("closing_at", ""),
                        "score": result.get("score"),
                        "recommendation": result.get("recommendation"),
                    })
                    notified += 1
                except Exception:        # noqa: BLE001 — notify is best-effort
                    pass
    return {"status": "DONE", "fetched": len(releases),
            "candidates": len(hits), "new": created, "notified": notified}
