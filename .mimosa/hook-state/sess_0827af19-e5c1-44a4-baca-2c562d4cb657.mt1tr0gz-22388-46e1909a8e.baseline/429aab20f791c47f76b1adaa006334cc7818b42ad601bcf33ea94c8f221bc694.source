"""Where trend observations come from. Each source is isolated and fail-closed.

A trend source is the only thing in the marketing cycle that talks to the
outside world to *gather* (the platform adapters *send*). Two rules shape
every source, and both come straight from the studio brief §۴:

  * **`sends_saba_data` is False, always.** Trend research is zero-class —
    it goes out, but it carries nothing of Saba's: no image, no name, no
    statistic. A source that needed her data to do its job would not be a
    trend source, it would be a leak. The flag exists so a future wiring
    can assert it rather than assume it.

  * **Failure is fail-closed and empty.** A network error, a bad status,
    an unparseable body all return an empty tuple, never a crash. A weekly
    cycle that gets zero observations is a quiet week; a weekly cycle that
    dies is a dead node. The scout's screen already refuses a candidate
    with no evidence, so an empty harvest costs one cycle, not the system.

The shipped sources today are a manual one (for partner/owner input and
for tests) and a disabled HTTP one (Google Trends alpha is application-
gated as of 2026; wiring it for real waits on that gate). The shape is
ready the day the key arrives — same as `remote_brain` waiting on its key.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol

from ..kernel.marketing_scout import TrendObservation


@dataclass(frozen=True)
class TrendQuery:
    """What a source is asked to look for. Carries no Saba data."""
    terms: tuple[str, ...]
    region: str | None = None
    since_epoch: int | None = None


class TrendSource(Protocol):
    """The contract every source implements.

    `source_id` is what gets stamped on every observation this source
    produces, so a human reading the week's harvest can see *where* a
    trend was seen, not just that it was.
    """

    source_id: str
    sends_saba_data: bool

    def observe(self, query: TrendQuery) -> tuple[TrendObservation, ...]: ...


class ManualTrendSource:
    """Observations handed in by a person — the partner, the owner, or a test.

    This is not a placeholder. The first weeks of any real account run on
    manual observation: Saba sees something on her feed, the owner reads an
    industry newsletter, and those are observations the automated sources
    will not have for months. Treating them as first-class (same shape,
    same screen, same memory) is what makes the manual-to-automated
    transition a change in *volume*, not in *kind*.
    """

    source_id = "manual"
    sends_saba_data = False

    def __init__(self, observations: tuple[TrendObservation, ...] = ()):
        self._observations = observations

    def add(self, obs: TrendObservation) -> None:
        self._observations = self._observations + (obs,)

    def observe(self, query: TrendQuery) -> tuple[TrendObservation, ...]:
        # Filter to the asked terms, case-insensitive, so a broad query does
        # not pull in observations meant for a different question.
        wanted = {t.lower() for t in query.terms}
        if not wanted:
            return self._observations
        return tuple(o for o in self._observations
                     if o.term.lower() in wanted)


@dataclass
class HttpTrendSource:
    """A source that calls an HTTP endpoint, fail-closed.

    The Google Trends API was in alpha as of mid-2025 and is application-
    gated; until a key is issued this source returns nothing rather than
    guessing. The wiring is here so the day the key arrives, enabling the
    source is a config change, not a code change — exactly the property
    `remote_brain` was built to have.

    `sends_saba_data` is False and is asserted at observe-time: a source
    that somehow had it flipped to True would be refusing to run, because
    the whole point of zero-class research is that it carries nothing of
    the partner's out.
    """

    source_id: str
    endpoint: str
    api_key: str = ""
    sends_saba_data: bool = False
    timeout_s: int = 20

    def observe(self, query: TrendQuery) -> tuple[TrendObservation, ...]:
        # The privacy guard, checked at call time. A source flagged as
        # sending Saba's data is not allowed to observe at all.
        if self.sends_saba_data:
            return ()

        if not self.api_key:
            # No key is a configuration state, not an outage. Empty harvest.
            return ()

        try:
            body = json.dumps({
                "terms": list(query.terms),
                "region": query.region,
                "since": query.since_epoch,
            }).encode("utf-8")
            req = urllib.request.Request(
                self.endpoint, data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {self.api_key}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                if resp.status != 200:
                    return ()
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError,
                ValueError, OSError):
            # Any failure → empty. A quiet week, not a dead node.
            return ()

        return self._parse(payload, query)

    def _parse(self, payload, query: TrendQuery) -> tuple[TrendObservation, ...]:
        """Turn a provider's JSON into kernel observations.

        Each provider shapes its response differently; this expects a list
        of objects with at least `term`, `observed_at`, and one of
        `count`/`rank`. Malformed entries are dropped, not fatal — one bad
        row must not void the whole harvest.
        """
        out: list[TrendObservation] = []
        items = payload.get("results") or payload.get("trends") or []
        if not isinstance(items, list):
            return ()
        import time as _t  # local; only for filling observed_at when absent
        for item in items:
            if not isinstance(item, dict):
                continue
            term = str(item.get("term", "")).strip()
            if not term:
                continue
            observed_at = int(item.get("observed_at", 0) or 0)
            if not observed_at:
                # A provider that omits the timestamp is not trusted to have
                # actually seen it. Fall back to now rather than refuse, but
                # only if a count/rank is present — evidence still required.
                observed_at = int(_t.time())
            count_value = item.get("count")
            rank_value = item.get("rank")
            try:
                obs = TrendObservation(
                    source_id=self.source_id,
                    term=term,
                    observed_at=observed_at,
                    count_value=float(count_value) if count_value is not None else None,
                    rank_value=int(rank_value) if rank_value is not None else None,
                    region=query.region,
                    source_url=item.get("url"),
                )
            except (ValueError, TypeError):
                continue
            except Exception:
                # TrendObservation raises FailClosedError if neither count
                # nor rank is present — that is the kernel refusing an
                # assertion. Drop the row, keep the harvest.
                continue
            out.append(obs)
        return tuple(out)


@dataclass
class TrendAggregator:
    """Runs several sources and concatenates their harvests.

    Order is stable (sources in the order given) so a week's observation
    list is reproducible from the same inputs. A source that returns ()
    contributes nothing and breaks nothing.
    """

    sources: tuple[TrendSource, ...] = field(default_factory=tuple)

    def observe(self, query: TrendQuery) -> tuple[TrendObservation, ...]:
        out: list[TrendObservation] = []
        for src in self.sources:
            try:
                out.extend(src.observe(query))
            except Exception:
                # A buggy source cannot be allowed to kill the cycle.
                continue
        return tuple(out)
