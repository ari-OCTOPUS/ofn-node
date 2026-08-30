"""
Worker A -- Researcher (KB-01, Phase 1)
Serper-powered search for suburb / competitor / keyword / pricing / pre-intent.

Tools: SerperClient (httpx).
Model: None in search path; Haiku reserved for LLM synthesis in Phase 2.

Governance:
  - read-only: never modifies external state.
  - All output source-labelled (KB-01 s4).
  - Cost tracked per call; SPEND_CAP enforced upstream by orchestrator.

Serper pricing (Jun 2026):
  Free tier: 2500 queries/month -> AUD $0.000
  Starter  : $50/month for 50000 queries -> ~AUD $0.00145/call
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from ..config import config
from ..governance import check_and_enforce
from ..resilience import call_with_retry

logger = logging.getLogger(__name__)

SERPER_URL = "https://google.serper.dev/search"
_SERPER_COST_AUD: float = 0.0  # free tier; update if on paid plan


@dataclass
class ResearchResult:
    query: str
    results: list[dict]    # [{"content": str, "source": str, "is_estimate": bool}]
    agent_id: str = "A_researcher"
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0


class SerperClient:
    """Thin httpx wrapper over Serper Google Search API. AU geo-targeted."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(self, query: str, num: int = 10) -> list[dict]:
        """
        Run a Google search via Serper.
        Returns raw list of {title, snippet, link} from organic results.
        Raises httpx.HTTPStatusError on 4xx / 5xx.
        """
        resp = httpx.post(
            SERPER_URL,
            headers={
                "X-API-KEY": self._api_key,
                "Content-Type": "application/json",
            },
            json={
                "q": query,
                "gl": "au",
                "hl": "en",
                "num": num,
                "location": "Sydney, New South Wales, Australia",
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return [
            {
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "link": r.get("link", ""),
            }
            for r in resp.json().get("organic", [])
        ]

    @staticmethod
    def to_labelled(raw: list[dict], is_estimate: bool = True) -> list[dict]:
        """Convert raw Serper hits to source-labelled format (KB-01 s4)."""
        return [
            {
                "content": r["title"] + " -- " + r["snippet"],
                "source": r["link"],
                "is_estimate": is_estimate,
            }
            for r in raw
            if r.get("snippet")
        ]


class Researcher:
    """
    Worker A: read-only research. All output source-labelled (KB-01 s4).
    Never publishes. Never modifies external state.
    """
    AGENT_ID = "A_researcher"

    def __init__(self) -> None:
        if config.SERPER_API_KEY:
            self._serper: Optional[SerperClient] = SerperClient(config.SERPER_API_KEY)
        else:
            self._serper = None
            logger.warning(
                "SERPER_API_KEY not set -- Worker A returns empty results. "
                "Add key to .env to activate Phase 1 search."
            )

    def _search(self, query: str, num: int = 8) -> list[dict]:
        """Safe Serper call -- returns [] on any error (non-fatal for MVP)."""
        if not self._serper:
            return []
        try:
            raw = call_with_retry(
                lambda: self._serper.search(query, num=num),
                agent_id=self.AGENT_ID,
                before_attempt=lambda: check_and_enforce(0.0, self.AGENT_ID),
                max_attempts=config.RETRY_MAX_ATTEMPTS,
                base_delay=config.RETRY_BASE_DELAY_SEC,
                max_delay=config.RETRY_MAX_DELAY_SEC,
            )
            return SerperClient.to_labelled(raw)
        except httpx.HTTPStatusError as exc:
            logger.error("Serper HTTP %s for query=%r", exc.response.status_code, query)
        except httpx.RequestError as exc:
            logger.error("Serper network error for query=%r: %s", query, exc)
        except Exception as exc:
            logger.error("Serper unexpected error for query=%r: %s", query, exc)
        return []

    def _cost_usd(self, n_calls: int) -> float:
        return round((_SERPER_COST_AUD * n_calls) / config.FX_AUD_USD, 8)

    def search_suburb(self, suburb: str) -> ResearchResult:
        """
        Demand, demographics, and competitor landscape for a suburb.
        2 Serper calls: review platforms + demographics signal.
        """
        results = self._search(
            "house painters " + suburb + " Sydney reviews "
            "site:hipages.com.au OR site:google.com OR site:serviceseeking.com.au",
            num=8,
        )
        results += self._search(
            suburb + " Sydney suburb demographics median household income 2024",
            num=4,
        )
        return ResearchResult(
            query="suburb:" + suburb,
            results=results,
            agent_id=self.AGENT_ID,
            cost_usd=self._cost_usd(2),
        )

    def search_competitor(self, suburb: str, service_type: str) -> ResearchResult:
        """
        Competitor pricing, reviews, and gaps for a suburb + service type.
        2 Serper calls: broad Google + Hipages marketplace (high-intent AU).
        """
        results = self._search(
            '"' + service_type + '" painters ' + suburb + ' Sydney price quote review 2024 2025',
            num=8,
        )
        results += self._search(
            "site:hipages.com.au " + service_type + " painters " + suburb + " Sydney",
            num=5,
        )
        return ResearchResult(
            query="competitor:" + suburb + ":" + service_type,
            results=results,
            agent_id=self.AGENT_ID,
            cost_usd=self._cost_usd(2),
        )

    def search_keyword_intent(self, suburb: str) -> ResearchResult:
        """
        High-intent keyword signals for local SEO targeting.
        3 Serper calls covering core intent patterns.
        """
        queries = [
            "painter " + suburb + " Sydney",
            "house painting " + suburb + " cost quote",
            "interior exterior painters " + suburb + " Sydney near me",
        ]
        results: list[dict] = []
        for q in queries:
            results += self._search(q, num=5)
        return ResearchResult(
            query="keywords:" + suburb,
            results=results,
            agent_id=self.AGENT_ID,
            cost_usd=self._cost_usd(len(queries)),
        )

    def search_market_pricing(self, suburb: str, service_type: str) -> ResearchResult:
        """
        Current market pricing for painting in a suburb.
        2 Serper calls: suburb-specific + AU trade pricing guides.
        """
        results = self._search(
            "house painting cost " + service_type + " " + suburb
            + " Sydney price per square metre 2024 2025",
            num=8,
        )
        results += self._search(
            "Australian painting cost guide " + service_type + " per sqm 2024 2025",
            num=4,
        )
        return ResearchResult(
            query="pricing:" + suburb + ":" + service_type,
            results=results,
            agent_id=self.AGENT_ID,
            cost_usd=self._cost_usd(2),
        )

    def search_pre_intent_signals(self, suburb: str) -> ResearchResult:
        """
        Pre-intent signals (KB-14): DA approvals, property sales, strata.
        Identifies prospects BEFORE they search for a painter.
        3 Serper calls.
        """
        results = self._search(
            "development application approved " + suburb
            + " NSW residential renovation extension 2024 2025",
            num=5,
        )
        results += self._search(
            "site:domain.com.au OR site:realestate.com.au " + suburb + " sold 2024 2025",
            num=5,
        )
        results += self._search(
            "strata capital works plan " + suburb + " Sydney painting maintenance 2024 2025",
            num=4,
        )
        return ResearchResult(
            query="pre_intent:" + suburb,
            results=results,
            agent_id=self.AGENT_ID,
            cost_usd=self._cost_usd(3),
        )
