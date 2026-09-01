"""Seek painter-job harvester — autonomous lead discovery (A0-A2).

buy.nsw is behind an Imperva CDN wall (403 on API, HTML on redirect);
Seek.com.au is open and returns real painter jobs in Sydney. This module
runs the same harvest contract as h1_harvest: fetch → filter → dedup →
create_lead → notify the owner queue (GREEN, cockpit-visible).

Scope discipline: this is NOT a tender — it is a job posting. Painting
jobs become leads (potential employers of painting services), not
government contracts. The lead_store's create_lead path is used, not
create_tender. No submit, no send, no external effect beyond the GET.
"""
from __future__ import annotations

import json
import re
import time
import urllib.request
from typing import Callable, Mapping

SEEK_URL = (
    "https://www.seek.com.au/painter-jobs/in-sydney-nsw"
)
TIMEOUT_S = 20
MAX_RETRIES = 2
USER_AGENT = "octopus-lead-harvester/1.0 (Ari; contact via repo owner)"

_TITLE = re.compile(
    r'data-automation="jobTitle"[^>]*>([^<]+)<')
_LOC = re.compile(
    r'data-automation="jobLocation"[^>]*>([^<]+)<')


class HarvestError(Exception):
    """Fetch/parse failure — park, never crash the loop."""


def fetch_html() -> str:
    last: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                SEEK_URL,
                headers={"User-Agent": USER_AGENT,
                         "Accept": "text/html"})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:              # noqa: BLE001
            last = exc
            time.sleep(2 * (attempt + 1))
    raise HarvestError(f"seek fetch failed after {MAX_RETRIES}: {last}")


def parse_jobs(html: str) -> list[dict]:
    """Extract job cards; paired title+location by document order."""
    titles = [t.strip() for t in _TITLE.findall(html)]
    locs = [l.strip() for l in _LOC.findall(html)]
    jobs = []
    for i, title in enumerate(titles):
        loc = locs[i] if i < len(locs) else "Sydney NSW"
        jobs.append({
            "title": title[:200],
            "location": loc[:120],
            "source": "seek",
            "slug": re.sub(r"[^a-z0-9]+", "-",
                           title.lower())[:80] + f"-{i}",
        })
    return jobs


def harvest(html: str) -> list[dict]:
    """Pure: HTML → painting-relevant lead payloads."""
    return [
        {"lead_id": f"seek:{j['slug']}",
         "channel": "seek",
         "name": j["title"],
         "suburb": j["location"],
         "source_url": SEEK_URL,
         "status": "new",
         "notes": f"Seek job posting: {j['title']} in {j['location']}"}
        for j in parse_jobs(html)
        if any(w in j["title"].lower()
               for w in ("paint", "decorat", "coating"))
    ]


def cycle(
    existing_ids: Callable[[], set],
    create_lead: Callable[[Mapping], dict],
    notify: Callable[[str, str, Mapping], bool] | None = None,
    *,
    fetch: Callable[[], str] = fetch_html,
) -> dict:
    """One cycle. Returns accounting; parks on feed failure."""
    try:
        html = fetch()
    except HarvestError as exc:
        return {"status": "PARKED", "reason": str(exc)[:200],
                "fetched": 0, "candidates": 0, "new": 0, "notified": 0}
    hits = harvest(html)
    seen = existing_ids()
    created, notified = 0, 0
    for hit in hits:
        if hit["lead_id"] in seen:
            continue
        result = create_lead(hit)
        if result.get("ok"):
            created += 1
            seen.add(hit["lead_id"])
            if notify is not None:
                try:
                    notify(hit["lead_id"], "LEAD_FOUND", {
                        "title": hit["name"][:80],
                        "location": hit["suburb"],
                    })
                    notified += 1
                except Exception:            # noqa: BLE001
                    pass
    return {"status": "DONE", "fetched": 1,
            "candidates": len(hits), "new": created, "notified": notified}
