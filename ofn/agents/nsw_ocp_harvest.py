"""NSW OCP registry harvester — real painting-service BUYERS.

The AusTender federal API works but has almost zero painting contracts
(0 in 30 days). The NSW OCP bulk download (via data.open-contracting.org)
has real painting contract AWARDS with named buyers who have paid for
painting services — these are repeat customers.

This module downloads the NSW annual JSONL.gz, extracts painting-related
contract awards, and creates leads with the buyer's contact information
where available. These are warm leads: they've already bought painting
services and will buy again.

Source: https://data.open-contracting.org/en/publication/11 (NSW
Treasury, CC-BY 3.0 AU license). One bulk download per run, not a live
feed — the annual file changes infrequently.
"""
from __future__ import annotations

import gzip
import json
import re
import urllib.request
from typing import Callable, Mapping

USER_AGENT = "octopus-demand-harvester/1.0 (Ari; repo: ari-OCTOPUS/ofn-node)"
BASE_URL = "https://data.open-contracting.org/en/publication/11/download"
TIMEOUT_S = 120

PAINTING_KEYWORDS = frozenset({
    "painting", "repainting", "repaint", "paint work", "paintwork",
    "external painting", "internal painting", "facade repaint",
    "coating", "surface coating", "protective coating",
})

# These are contract AWARDS — the buyer has already paid for painting.
# They are warm leads for the NEXT round of painting work.
DEMAND_SIGNALS = frozenset({
    "purchase order", "contract award", "work order", "quote",
    "as per quote", "engagement of",
})


def download_nsw(year: int = 2025) -> bytes:
    """One bulk GET of the NSW annual JSONL.gz file."""
    url = f"{BASE_URL}?name={year}.jsonl.gz"
    req = urllib.request.Request(url, headers={
        "Accept": "application/gzip", "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return resp.read()


def is_painting_award(release: Mapping) -> bool:
    """True if any award item or title mentions painting services."""
    text = json.dumps(release).lower()
    return any(kw in text for kw in PAINTING_KEYWORDS)


def is_supply_side(release: Mapping) -> bool:
    """These are awards (already paid) so always demand-side."""
    return False


def extract_buyer_leads(releases: list[Mapping]) -> list[dict]:
    """Extract painting-service buyers from NSW award releases."""
    buyers: dict[str, dict] = {}
    for release in releases:
        if not is_painting_award(release):
            continue
        for award in release.get("awards", []):
            buyer = award.get("buyer", {})
            name = str(buyer.get("name", "") or "").strip()
            if not name:
                continue
            contact = buyer.get("contactPoint", {})
            val = (award.get("value", {}) or {}).get("amount") or 0
            items = award.get("items", [])
            desc = " ".join(
                re.sub(r"<[^>]+>", " ", str(i.get("description", "")))
                for i in items)[:200].strip()
            if name not in buyers:
                buyers[name] = {
                    "lead_id": f"nsw_ocp_buyer:{re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')[:60]}",
                    "channel": "nsw_ocp_registry",
                    "name": name[:200],
                    "contact_person": str(contact.get("name", "") or "")[:120],
                    "email": str(contact.get("email", "") or "")[:200],
                    "phone": str(contact.get("telephone", "") or "")[:40],
                    "total_awarded_aud": 0,
                    "contract_count": 0,
                    "last_work_description": desc,
                    "source_url": f"https://data.open-contracting.org/en/publication/11",
                    "status": "warm_lead",
                    "notes": f"Repeat NSW painting buyer",
                }
            buyers[name]["total_awarded_aud"] += val
            buyers[name]["contract_count"] += 1
            if desc:
                buyers[name]["last_work_description"] = desc
    return sorted(buyers.values(),
                  key=lambda b: -b["total_awarded_aud"])


def harvest(data: bytes) -> list[dict]:
    """Pure: decompress + parse + extract painting-service buyer leads."""
    text = gzip.decompress(data).decode("utf-8", "replace")
    releases = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            releases.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return extract_buyer_leads(releases)
