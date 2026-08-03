"""Tools exposed to the Hunter agent via Anthropic tool-use."""
from __future__ import annotations

import json
import logging
from datetime import datetime

import httpx
from bs4 import BeautifulSoup
from tavily import TavilyClient

from config import settings
from db import Channel, get_session

logger = logging.getLogger(__name__)

_tavily = TavilyClient(api_key=settings.tavily_api_key)


# ---------- Tool implementations ----------

def web_search(query: str, max_results: int = 8) -> str:
    """Run a Tavily web search. Returns JSON string."""
    try:
        res = _tavily.search(query=query, search_depth="advanced", max_results=max_results)
        out = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", "")[:500],
            }
            for r in res.get("results", [])
        ]
        return json.dumps(out, ensure_ascii=False)
    except Exception as e:
        logger.exception("web_search failed")
        return json.dumps({"error": str(e)})


def fetch_page(url: str) -> str:
    """Fetch a page, return cleaned text (max 8000 chars)."""
    try:
        with httpx.Client(
            timeout=20, follow_redirects=True, headers={"User-Agent": "paint-leads-bot/0.1"}
        ) as c:
            r = c.get(url)
            r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for s in soup(["script", "style", "noscript"]):
            s.decompose()
        text = " ".join(soup.get_text(" ", strip=True).split())[:8000]
        return text or "[empty page]"
    except Exception as e:
        return f"[fetch failed: {e}]"


def save_channel(
    name: str,
    type: str,
    url: str,
    access: str,
    cost_to_enter: str = "free",
    lead_volume: str = "medium",
    typical_value: str = "$30K-250K",
    competition: str = "medium",
    geo: str = "Sydney",
    sample_lead: str = "",
    notes: str = "",
    score: int = 50,
) -> str:
    """Persist a candidate channel to the DB with status=pending."""
    with get_session() as s:
        # Skip duplicates on URL
        from sqlmodel import select

        existing = s.exec(select(Channel).where(Channel.url == url)).first()
        if existing:
            return json.dumps({"saved": False, "reason": "duplicate-url", "id": existing.id})
        ch = Channel(
            name=name[:200],
            type=type,
            url=url,
            access=access,
            cost_to_enter=cost_to_enter,
            lead_volume=lead_volume,
            typical_value=typical_value,
            competition=competition,
            geo=geo[:200],
            sample_lead=sample_lead[:800],
            notes=notes[:1500],
            score=max(0, min(100, score)),
            status="pending",
            discovered_at=datetime.utcnow(),
        )
        s.add(ch)
        s.commit()
        s.refresh(ch)
        return json.dumps({"saved": True, "id": ch.id})


# ---------- Anthropic tool schema ----------

TOOL_SCHEMA = [
    {
        "name": "web_search",
        "description": "Search the web with Tavily. Use for discovering new lead channels.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 8},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": "Fetch and clean text of a URL. Use to verify a candidate channel.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "save_channel",
        "description": (
            "Persist a verified candidate channel for operator approval. "
            "Only save channels that are real, NSW-relevant, and have at "
            "least one sample lead/opportunity confirmed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": [
                        "gov",
                        "commercial",
                        "strata",
                        "insurance",
                        "fm",
                        "remedial",
                        "developer",
                        "council",
                        "architect",
                        "education",
                        "healthcare",
                        "hospitality",
                        "transport",
                        "industry-niche",
                    ],
                },
                "url": {"type": "string"},
                "access": {
                    "type": "string",
                    "enum": [
                        "open-tender",
                        "panel-application",
                        "cold-outreach",
                        "api",
                        "scrape",
                        "email-alert",
                    ],
                },
                "cost_to_enter": {"type": "string", "enum": ["free", "$", "$$", "$$$"]},
                "lead_volume": {"type": "string", "enum": ["low", "medium", "high"]},
                "typical_value": {"type": "string"},
                "competition": {"type": "string", "enum": ["low", "medium", "high"]},
                "geo": {"type": "string"},
                "sample_lead": {"type": "string"},
                "notes": {"type": "string"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
            },
            "required": ["name", "type", "url", "access", "notes", "score"],
        },
    },
]


def dispatch_tool(name: str, args: dict) -> str:
    if name == "web_search":
        return web_search(**args)
    if name == "fetch_page":
        return fetch_page(**args)
    if name == "save_channel":
        return save_channel(**args)
    return json.dumps({"error": f"unknown tool: {name}"})
