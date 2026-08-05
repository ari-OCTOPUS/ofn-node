"""The weekly marketing cycle — the engine that ties the parts together.

This is the adapter that orchestrates one weekly run end to end:

    sources.observe(query)
        → observations recorded
        → scout.triage(observations, persisted_memory)
        → fresh candidates kept, refused counted (not dropped)
        → memory persisted back to the store
        → a focus question derived from measured gaps
        → the week opened with that focus

It is deliberately *not* in the kernel: it touches the network (via
sources), the store (via marketing_store), and the clock (via now_epoch_s).
The kernel decides what to refuse; this module decides in what order to
ask, and what to write down.

What this does NOT do, on purpose:

  * It does not call the hosted model. Producing actual candidate ideas
    from observations is the model's job, and that call belongs behind
    the same routing/quota/scrub machinery every other brain call uses.
    This engine hands the model a brief (the focus + the rejection list)
    and accepts the candidates it returns; it does not itself prompt.

  * It does not publish, route to platforms, or touch the outbox. A
    candidate that survives triage becomes a *proposal for Saba*, not a
    post. Going from "she picked this idea" to "a variant in the outbox"
    is a separate, later step (the dashboard + content router).

  * It does not auto-advance weeks. Opening a new week is a decision, not
    a schedule; the owner closes the old one and this opens the next.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..kernel.marketing_scout import (
    Candidate, Disposition, Memory, Note, TrendObservation, brief,
    research_focus, triage,
)
from .marketing_store import MarketingStore
from .trend_sources import TrendAggregator, TrendQuery


@dataclass(frozen=True)
class CycleResult:
    """What one weekly run produced. Returned so the caller (the dashboard,
    the owner panel, a test) can show it without re-running the cycle."""
    week_id: str
    style_id: str
    focus_text: str
    observations_kept: int
    fresh_candidates: tuple[Candidate, ...]
    refused_count: int
    research_questions: tuple[str, ...]


class WeeklyCycle:
    """One weekly research cycle, wired to a store and a set of sources."""

    def __init__(self, store: MarketingStore,
                 sources: TrendAggregator | None = None):
        self.store = store
        self.sources = sources or TrendAggregator(())

    def run(self, *, tenant: str, week_id: str, starts_at: int,
            style_id: str, query: TrendQuery,
            candidates: tuple[Candidate, ...],
            tried_styles: Mapping[str, int] | None = None,
            last_week_style: str | None = None,
            now_epoch_s: int) -> CycleResult:
        """Run one cycle. See module docstring for what it does and does not.

        `candidates` are the model's proposals for this week, already
        constructed by the caller. This engine does not call the model; it
        triages whatever candidates it is given against the persisted
        memory, which is the part that has to be done in-process and in-
        order with the store.
        """
        # 1) Gather observations from every source. A source that fails
        # returns () and the cycle continues — a quiet source is not a
        # dead cycle.
        observations = self.sources.observe(query)
        if observations:
            self.store.record_observations(
                tenant, week_id, observations, now_epoch_s=now_epoch_s)

        # 2) Load the persisted rejection memory. This is the line that
        # makes the ratchet survive reboots — without it, the model would
        # re-propose last week's refused idea every Monday.
        memory = self.store.load_memory(tenant)

        # 3) Triage. The kernel refuses what it must; we keep the rest and
        # count the refused. Refused is *not* dropped — the caller sees the
        # count so a quiet week is distinguishable from a broken pipeline.
        fresh, refused = triage(
            candidates, memory, now_epoch_s=now_epoch_s)

        # 4) Persist the fresh candidates as PROPOSED, so a re-run of the
        # same week does not surface them twice. The ratchet turns PROPOSED
        # into a duplicate refusal on the next pass.
        for c in fresh:
            self.store.remember(
                tenant, c,
                Note(c.key, Disposition.PROPOSED, "shown this week",
                     now_epoch_s),
                rejected_by="cycle", now_epoch_s=now_epoch_s)
            # Reload so the just-recorded PROPOSED is visible downstream.
            memory = self.store.load_memory(tenant)

        # 5) Derive the focus from measured gaps, not from novelty. The
        # ordering inside research_focus is the argument.
        questions = research_focus(
            memory,
            last_week_style=last_week_style,
            tried_styles=tried_styles or {},
        )
        # The focus text the partner sees is the joined questions; the
        # dashboard may present them as a list instead.
        focus_text = "\n".join(questions)

        # 6) Open the week with that focus. Re-runnable: the same week_id
        # replaces its row, which is how a cycle resumes after a crash.
        self.store.open_week(
            tenant, week_id, starts_at=starts_at, style_id=style_id,
            focus_text=focus_text, now_epoch_s=now_epoch_s)

        return CycleResult(
            week_id=week_id, style_id=style_id, focus_text=focus_text,
            observations_kept=len(observations),
            fresh_candidates=fresh, refused_count=len(refused),
            research_questions=questions,
        )

    def reject(self, *, tenant: str, candidate: Candidate, reason: str,
               rejected_by: str, now_epoch_s: int,
               soft: bool = False) -> None:
        """Record that the partner (or owner) refused an idea.

        Hard by default — a structural refusal (banned, wrong platform,
        not safe) never comes back. Soft when the reason is circumstantial
        ("the source was in beta"); the scout's cooldown decides when it
        may return.
        """
        disp = Disposition.REJECTED_SOFT if soft else Disposition.REJECTED_HARD
        self.store.remember(
            tenant, candidate,
            Note(candidate.key, disp, reason, now_epoch_s),
            rejected_by=rejected_by, now_epoch_s=now_epoch_s)

    def accept(self, *, tenant: str, candidate: Candidate,
               accepted_by: str, now_epoch_s: int) -> None:
        """Record that the partner is acting on an idea."""
        self.store.remember(
            tenant, candidate,
            Note(candidate.key, Disposition.ACCEPTED, "partner accepted",
                 now_epoch_s),
            rejected_by=accepted_by, now_epoch_s=now_epoch_s)
