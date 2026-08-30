"""AusTender — federal tenders via the official OCDS API (no scraping).

Endpoint (public, no API key):
  https://api.tenders.gov.au/ocds/findByDates/atmPublished/{from}/{to}

Returns OCDS 1.1 release packages for ATMs (Approach to Market = open
tenders). We pull a rolling window, keyword-filter for painting relevance,
and drop ATMs that are clearly for other states only.

Docs: https://github.com/austender/austender-ocds-api
Verify live (on your machine):  python test_run.py --source austender
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta

import httpx

from db import Lead
from harvesters.base import Harvester
from harvesters.keywords import is_paint_relevant

logger = logging.getLogger(__name__)

API_BASE = "https://api.tenders.gov.au/ocds/findByDates/atmPublished"
WINDOW_DAYS = 4   # rolling lookback; dedupe makes overlap harmless
MAX_PAGES = 5     # safety cap on OCDS paging

# Word-boundary matching on the RAW json — plain substrings are dangerous
# ("service" contains "vic"). Unknown location → keep; scorer decides.
_NSW_RE = re.compile(r"\b(NSW|New South Wales|ACT|Australian Capital Territory)\b")
_OTHER_RE = re.compile(
    r"\b(VIC|Victoria|QLD|Queensland|WA|Western Australia|SA|South Australia"
    r"|TAS|Tasmania|NT|Northern Territory)\b"
)


def _nsw_relevant(raw: str) -> bool:
    if _NSW_RE.search(raw):
        return True
    if _OTHER_RE.search(raw):
        return False
    return True  # location unknown → keep


def parse_release(rel: dict) -> Lead | None:
    """One OCDS release → Lead (or None if irrelevant). Pure function — tested."""
    tender = rel.get("tender") or {}
    title = (tender.get("title") or "").strip()
    desc = (tender.get("description") or "").strip()
    if not (title or desc):
        return None
    if not is_paint_relevant(f"{title} {desc}"):
        return None

    raw = json.dumps(rel, ensure_ascii=False)
    if not _nsw_relevant(raw):
        return None

    ocid = str(rel.get("ocid") or rel.get("id") or "").strip()
    if not ocid:
        return None

    value = None
    amount = (tender.get("value") or {}).get("amount")
    if isinstance(amount, (int, float)):
        value = int(amount)

    deadline = None
    end = (tender.get("tenderPeriod") or {}).get("endDate") or ""
    if end:
        try:
            deadline = datetime.fromisoformat(end.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            pass

    url = ""
    for doc in tender.get("documents") or []:
        if isinstance(doc, dict) and doc.get("url"):
            url = doc["url"]
            break
    if not url:
        url = "https://www.tenders.gov.au/atm"

    buyer = (rel.get("buyer") or {}).get("name") or ""
    description = desc or title
    if buyer:
        description = f"{description}\n\nBuyer: {buyer}"

    return Lead(
        source="austender",
        external_id=ocid[:300],
        title=(title or desc)[:200],
        description=description[:3000],
        url=url,
        value_aud=value,
        deadline=deadline,
        suburb="",
        category="gov",
        raw_json=raw[:5000],
    )


def parse_releases(package: dict) -> list[Lead]:
    leads = []
    for rel in package.get("releases") or []:
        if isinstance(rel, dict):
            lead = parse_release(rel)
            if lead:
                leads.append(lead)
    return leads


class AusTenderHarvester(Harvester):
    name = "austender"
    interval_minutes = 60  # API is cheap, but hourly is plenty for tenders

    async def fetch(self) -> list[Lead]:
        now = datetime.utcnow()
        frm = (now - timedelta(days=WINDOW_DAYS)).strftime("%Y-%m-%d")
        to = now.strftime("%Y-%m-%d")
        url: str | None = f"{API_BASE}/{frm}/{to}"
        leads: list[Lead] = []
        pages = 0
        async with httpx.AsyncClient(
            timeout=30, headers={"User-Agent": "paint-leads-bot/0.2"}
        ) as client:
            while url and pages < MAX_PAGES:
                r = await client.get(url)
                r.raise_for_status()
                package = r.json()
                leads.extend(parse_releases(package))
                url = (package.get("links") or {}).get("next")
                pages += 1
        return leads
