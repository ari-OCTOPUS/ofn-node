"""AusTender — federal tenders.

DISABLED for MVP: tenders.gov.au runs a JavaScript-heavy search interface that
returns 404 for direct URL fetches. Working integration needs Playwright OR
deep URL reverse-engineering (their auth params change).

For Sydney-NSW painting work, NSW eTendering / council tenders are more
relevant anyway. The Hunter agent (via Tavily web search) will discover
federal tenders when relevant — no need for a dedicated harvester at MVP scale.

To re-enable later:
  - Install Playwright, render https://www.tenders.gov.au/Atm with JS
  - Find the AJAX endpoint they hit and call it with proper headers
  - Or subscribe to a paid alerts service (ConnectID, BidPilot AU)
"""
from __future__ import annotations

from db import Lead
from harvesters.base import Harvester


class AusTenderHarvester(Harvester):
    name = "austender"

    async def fetch(self) -> list[Lead]:
        return []
