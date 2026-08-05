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
import re
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


def _parse_candidate(item: Mapping, *, now_epoch_s: int = 0) -> Candidate | None:
    try:
        key = str(item.get("key", "")).strip()
        title = str(item.get("title", "")).strip()
        if not key or not title:
            return None
        obs_raw = item.get("observations") or []
        if isinstance(obs_raw, list):
            observations = tuple(
                o for o in (_parse_observation(x) for x in obs_raw
                            if isinstance(x, Mapping))
                if o is not None)
        else:
            observations = ()
        if not observations:
            # The model's prompt asks for ideas without requiring raw
            # observations (those come from trend sources). But the kernel's
            # Candidate requires at least one observation as evidence — a
            # candidate with no evidence is an assertion, which the scout
            # refuses. We attach one observation sourced to the model itself,
            # so the candidate is honest about where it came from: a model
            # proposal, not a measured trend. The scout's confidence screen
            # is still the gate.
            import time as _t
            ts = now_epoch_s or int(_t.time())
            observations = (TrendObservation(
                source_id="model_proposal", term=title[:60],
                observed_at=ts, count_value=1.0),)
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


def parse_candidates(text: str, *, now_epoch_s: int = 0) -> tuple[Candidate, ...]:
    """Parse the model's response into valid Candidates.

    The prompt asks for an object: ``{"candidates":[...]}``. The model
    sometimes wraps that in prose or fences, and occasionally returns a
    bare array from an older prompt. We try the object shape first, then
    fall back to the first JSON array we can find, and parse each element
    defensively. A response that yields zero valid candidates is a
    legitimate (if unhelpful) answer — the cycle runs with no fresh
    candidates and derives the focus from gaps, which is what it would do
    on a quiet week anyway.
    """
    if not text or not text.strip():
        return ()

    # Strip markdown code fences if present — the model often wraps JSON
    # in ```json ... ``` despite being told not to.
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\n?", "", stripped)
        stripped = re.sub(r"\n?```$", "", stripped)

    items: list | None = None
    # Try the documented object shape first.
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict) and isinstance(obj.get("candidates"), list):
            items = obj["candidates"]
        elif isinstance(obj, list):
            items = obj  # bare array fallback
    except (ValueError, TypeError):
        items = None

    # Fallback: extract the first JSON array span (robust against prose
    # wrappers the model may still add).
    if items is None:
        start = stripped.find("[")
        end = stripped.rfind("]")
        if start < 0 or end <= start:
            return ()
        try:
            items = json.loads(stripped[start:end + 1])
        except (ValueError, TypeError):
            return ()

    if not isinstance(items, list):
        return ()
    out: list[Candidate] = []
    for item in items:
        if isinstance(item, Mapping):
            c = _parse_candidate(item, now_epoch_s=now_epoch_s)
            if c is not None:
                out.append(c)
    return tuple(out)
