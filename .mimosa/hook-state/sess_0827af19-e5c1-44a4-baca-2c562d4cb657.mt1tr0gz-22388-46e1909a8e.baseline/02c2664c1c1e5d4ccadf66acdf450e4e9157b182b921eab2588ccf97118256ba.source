"""PlanningAlerts.org.au — DAs from all NSW councils. Free JSON API.

Rate limits (free tier): 1 request/second, 1000 requests/DAY.
Quota math: 20 authorities × 8 runs/day (every 3h) = 160 req/day ✓
(The old 15-minute cadence would have been 1,920 req/day — over the limit.)
DAs are published daily anyway; 3-hourly is more than enough.
"""
from __future__ import annotations

import asyncio
import json

import httpx

from config import settings
from db import Lead
from harvesters.base import Harvester
from harvesters.keywords import is_paint_relevant

# Sydney metro authorities — extend as needed
NSW_AUTHORITIES = [
    "sydney",
    "north_sydney",
    "willoughby",
    "lane_cove",
    "mosman",
    "waverley",
    "woollahra",
    "randwick",
    "bayside",
    "canada_bay",
    "inner_west",
    "parramatta",
    "ryde",
    "ku-ring-gai",
    "hornsby",
    "northern_beaches",
    "burwood",
    "strathfield",
    "georges_river",
    "sutherland",
]

# PlanningAlerts allows 1 request per second per key — be polite
REQUEST_INTERVAL_SEC = 1.2


async def _fetch_one(client: httpx.AsyncClient, auth: str, attempts: int = 3) -> dict | list:
    """Fetch one authority with retry on 429."""
    delay = 2.0
    for i in range(attempts):
        try:
            r = await client.get(
                f"https://api.planningalerts.org.au/authorities/{auth}/applications.json",
                params={"key": settings.planning_alerts_api_key, "page": 1},
            )
            if r.status_code == 429:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and i < attempts - 1:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            raise
    return {}


class PlanningAlertsHarvester(Harvester):
    name = "planning_alerts"
    interval_minutes = 180  # every 3h — keeps us at ~160 req/day (limit: 1000)

    async def fetch(self) -> list[Lead]:
        leads: list[Lead] = []
        async with httpx.AsyncClient(timeout=30) as client:
            for auth in NSW_AUTHORITIES:
                try:
                    payload = await _fetch_one(client, auth)
                except Exception as e:
                    print(f"PlanningAlerts {auth} failed: {e}")
                    await asyncio.sleep(REQUEST_INTERVAL_SEC)
                    continue

                # API may return a list directly, OR {"applications": [...]}
                if isinstance(payload, list):
                    items = payload
                elif isinstance(payload, dict):
                    items = payload.get("applications", [])
                else:
                    items = []

                for item in items:
                    app = item.get("application", item) if isinstance(item, dict) else {}
                    if not app:
                        continue

                    desc = app.get("description") or ""
                    if not is_paint_relevant(desc):
                        continue

                    ext_id = f"{auth}-{app.get('council_reference','')}"
                    if not ext_id.strip("-"):
                        continue

                    leads.append(
                        Lead(
                            source=self.name,
                            external_id=ext_id,
                            title=desc[:200],
                            description=desc,
                            url=app.get("info_url") or app.get("comment_url") or "",
                            suburb=app.get("address", ""),
                            category="da",
                            raw_json=json.dumps(app)[:5000],
                        )
                    )

                # Be polite — stay under 1 req/sec
                await asyncio.sleep(REQUEST_INTERVAL_SEC)

        return leads
