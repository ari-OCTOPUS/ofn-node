"""Helpers for the marketing cycle's model round-trip.

Two jobs, both small enough to live together:

1. Render the scout's brief as JSON for the model prompt — safely, so a
   future field that is not JSON-serialisable cannot crash the cycle.

2. Parse the model's candidate ideas back into kernel `Candidate` objects.
   The model is trusted to produce JSON; it is not trusted to produce
   *valid* Candidates. Every field is checked, every malformed entry is
   dropped, and a single bad row never voids the harvest.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from ..kernel.marketing_scout import (
    Candidate, TrendObservation,
)
from ..kernel.errors import FailClosedError


def json_dumps_safe(obj: Any) -> str:
    """json.dumps that never raises. Falls back to str() on any failure."""
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return str(obj)


def _parse_observation(item: Mapping) -> TrendObservation | None:
    try:
        term = str(item.get("term", "")).strip()
        if not term:
            return None
        observed_at = int(item.get("observed_at", 0) or 0)
        count = item.get("count_value")
        rank = item.get("rank_value")
        return TrendObservation(
            source_id=str(item.get("source_id", "model")),
            term=term,
            observed_at=observed_at,
            count_value=float(count) if count is not None else None,
            rank_value=int(rank) if rank is not None else None,
            region=item.get("region"),
            source_url=item.get("source_url"),
        )
    except (ValueError, TypeError):
        return None
    except FailClosedError:
        # The kernel refuses an observation with no observed_at or no
        # count/rank. That is the kernel doing its job; drop the row.
        return None


def _parse_candidate(item: Mapping) -> Candidate | None:
    try:
        key = str(item.get("key", "")).strip()
        title = str(item.get("title", "")).strip()
        if not key or not title:
            return None
        obs_raw = item.get("observations") or []
        if not isinstance(obs_raw, list):
            return None
        observations = tuple(
            o for o in (_parse_observation(x) for x in obs_raw
                        if isinstance(x, Mapping))
            if o is not None)
        if not observations:
            # A candidate with no usable observations is an assertion; the
            # scout would refuse it anyway, so we drop it here.
            return None
        confidence = float(item.get("confidence", 0.0) or 0.0)
        return Candidate(
            key=key, title=title,
            style_id=str(item.get("style_id", "")),
            framing=str(item.get("framing", "beauty")),
            observations=observations,
            confidence=confidence,
        )
    except (ValueError, TypeError):
        return None
    except FailClosedError:
        return None


def parse_candidates(text: str) -> tuple[Candidate, ...]:
    """Parse the model's response into valid Candidates.

    The model is asked for a JSON array; it sometimes wraps that in prose
    or fences. We extract the first JSON array we can find and parse each
    element defensively. A response that yields zero valid candidates is
    a legitimate (if unhelpful) answer — the cycle runs with no fresh
    candidates and derives the focus from gaps, which is what it would do
    on a quiet week anyway.
    """
    if not text or not text.strip():
        return ()
    # Find the first '[' ... ']' span. Cheap and robust against the common
    # "Here are the ideas: [...]" wrapper.
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        return ()
    chunk = text[start:end + 1]
    try:
        items = json.loads(chunk)
    except (ValueError, TypeError):
        return ()
    if not isinstance(items, list):
        return ()
    out: list[Candidate] = []
    for item in items:
        if isinstance(item, Mapping):
            c = _parse_candidate(item)
            if c is not None:
                out.append(c)
    return tuple(out)
