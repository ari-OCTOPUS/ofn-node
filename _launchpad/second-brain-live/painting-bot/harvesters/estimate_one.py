"""EstimateOne — NSW tenders.

NOTE: EstimateOne sits behind Cloudflare anti-bot — httpx requests get HTTP 403
("Just a moment..." challenge). We need a real browser to pass the JS check.

For MVP, this harvester is disabled (returns []). Two options to enable later:
  1. Install Playwright (`pip install playwright && playwright install chromium`)
     and rewrite fetch() with `await page.goto(LIST_URL)`.
  2. Use a CAPTCHA-aware proxy service (ScrapingBee / Bright Data, paid).

Until then, EstimateOne content reaches us via the Hunter agent (which uses
Tavily search results + URL fetches as fallback) or via paid subscription's
direct API (phase 2).
"""
from __future__ import annotations

from db import Lead
from harvesters.base import Harvester


class EstimateOneHarvester(Harvester):
    name = "estimate_one"

    async def fetch(self) -> list[Lead]:
        # Disabled for MVP — see module docstring for re-enable path
        return []
