"""Scorer — replaces LLM-based scoring with the YAML-driven LeadScorer.

Public interface (unchanged so callers don't break):
    score_lead(lead: Lead) -> (score:int, category:str, reason:str)
    score_unscored() -> int    # number of leads scored

Internally:
    Builds a dict expected by LeadScorer from the SQLModel Lead row,
    extracting lat/lng/cost_of_development from raw_json if available.
    Returns the deterministic YAML-computed score.

LLM scoring is removed for routine leads — it was expensive, slow, and
non-deterministic for a task that's really pattern-matching keywords.
The Hunter agent still uses LLM (where reasoning matters).
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

from sqlmodel import select

from db import Lead, get_session
from lead_scorer import LeadScorer, ScoredLead

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _scorer() -> LeadScorer:
    return LeadScorer()


def _lead_to_dict(lead: Lead) -> dict:
    """Map a Lead row to the dict shape LeadScorer expects."""
    raw: dict = {}
    if lead.raw_json:
        try:
            raw = json.loads(lead.raw_json)
            if not isinstance(raw, dict):
                raw = {}
        except Exception:
            raw = {}

    return {
        "source": lead.source,
        "description": lead.description or lead.title,
        "address": lead.suburb or raw.get("address", ""),
        "council": raw.get("council") or raw.get("authority", {}).get("full_name")
            if isinstance(raw.get("authority"), dict) else raw.get("council", ""),
        "cost_of_development": raw.get("cost_of_development"),
        "lat": raw.get("lat"),
        "lng": raw.get("lng"),
        "url": lead.url,
    }


def score_lead(lead: Lead) -> tuple[int, str, str]:
    """Returns (score, category, reason) — same interface as before."""
    try:
        result: ScoredLead = _scorer().score(_lead_to_dict(lead))
        reason = f"action={result.action} | " + "; ".join(result.reasons)
        return result.score, result.category, reason[:500]
    except Exception as e:
        logger.warning("Scorer failed for lead %s: %s", lead.id, e)
        return 50, "other", f"scorer-error: {type(e).__name__}"


def score_unscored() -> int:
    """Score every lead with score == 0. Returns count scored."""
    with get_session() as s:
        rows = list(s.exec(select(Lead).where(Lead.score == 0)).all())
        count = 0
        for lead in rows:
            sc, cat, reason = score_lead(lead)
            lead.score = sc
            if cat and cat != "other":
                lead.category = cat
            lead.score_reason = reason
            s.add(lead)
            count += 1
        s.commit()
        return count
