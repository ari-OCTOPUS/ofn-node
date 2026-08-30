"""NSW eTendering (tenders.nsw.gov.au) — current open RFTs via public RSS.

The most Sydney-relevant tender source. Feed routes on this site have changed
over the years, so we try several candidates and use the first that returns
entries. Parsing is stdlib-only (RSS 2.0 + Atom, namespace-agnostic).

If every candidate fails we log loudly and return [] — the failure is visible
in RunLog and /stats. Fallback if RSS ever disappears: IMAP parsing of the
official email alerts (roadmap).

Verify live (on your machine):  python test_run.py --source nsw_etendering
"""
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET

import httpx

from db import Lead
from harvesters.base import Harvester
from harvesters.keywords import is_paint_relevant

logger = logging.getLogger(__name__)

FEED_CANDIDATES: tuple[str, ...] = (
    "https://www.tenders.nsw.gov.au/?event=public.rss.RFT",
    "https://www.tenders.nsw.gov.au/?event=public.rss",
    "https://www.tenders.nsw.gov.au/public.rss.cfm?event=public.rss.RFT",
)

_TAG_RE = re.compile(r"<[^>]+>")


def _text(el) -> str:
    return (el.text or "").strip() if el is not None else ""


def _local(tag) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def parse_feed(xml_text: str) -> list[dict]:
    """RSS 2.0 or Atom → [{id, title, link, description}]. Pure function — tested."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    entries: list[dict] = []
    for node in root.iter():
        if _local(node.tag) not in ("item", "entry"):
            continue
        e = {"id": "", "title": "", "link": "", "description": ""}
        for child in node:
            name = _local(child.tag)
            if name == "title":
                e["title"] = _text(child)
            elif name == "link":
                e["link"] = _text(child) or (child.get("href") or "")
            elif name in ("description", "summary", "content"):
                e["description"] = _TAG_RE.sub(" ", _text(child)).strip()
            elif name in ("guid", "id"):
                e["id"] = _text(child)
        if e["title"] or e["link"]:
            e["id"] = e["id"] or e["link"] or e["title"]
            entries.append(e)
    return entries


def entries_to_leads(entries: list[dict], source: str = "nsw_etendering") -> list[Lead]:
    """Keyword-filter feed entries into Lead rows. Pure function — tested."""
    leads: list[Lead] = []
    for e in entries:
        if not is_paint_relevant(f"{e.get('title', '')} {e.get('description', '')}"):
            continue
        leads.append(
            Lead(
                source=source,
                external_id=(e.get("id") or "")[:300],
                title=(e.get("title") or "")[:200],
                description=(e.get("description") or "")[:2000],
                url=e.get("link") or "",
                category="gov",
                raw_json="",
            )
        )
    return leads


class NswEtenderingHarvester(Harvester):
    name = "nsw_etendering"
    interval_minutes = 60

    async def fetch(self) -> list[Lead]:
        entries: list[dict] = []
        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; paint-leads-bot/0.2)"},
        ) as client:
            for feed_url in FEED_CANDIDATES:
                try:
                    r = await client.get(feed_url)
                    if r.status_code != 200 or "<" not in r.text[:300]:
                        continue
                    entries = parse_feed(r.text)
                    if entries:
                        break
                except Exception as e:
                    logger.warning("NSW eTendering feed %s failed: %s", feed_url, e)
        if not entries:
            logger.warning(
                "NSW eTendering: no feed candidate returned entries — "
                "site layout may have changed; check FEED_CANDIDATES."
            )
            return []
        return entries_to_leads(entries, source=self.name)
