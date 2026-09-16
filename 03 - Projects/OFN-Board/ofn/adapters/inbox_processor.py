"""Dry-run inbox processor: claim → validate shape → mark held/processed.

This is a *dry run* by design. It claims pending inbox items and validates
their shape (vendor_event_id present, size sane) but it does NOTHING else:
no outbox enqueue, no HTTP outbound, no fact writes, no email. The megaprompt
forbids a real processor until a vendor and its HMAC secret exist; this
exists so the state machine (claim/mark/recover) is exercised for real and
any future real processor has a proven skeleton.

FORBIDDEN here, structurally: outbox, transport, fact store. If a future
developer wires those in, this module's contract is broken — review it the
same way a sender review would go.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class ProcessStats:
    claimed: int = 0
    processed: int = 0
    held: int = 0
    errors: int = 0

    def as_dict(self) -> Mapping[str, int]:
        return {"claimed": self.claimed, "processed": self.processed,
                "held": self.held, "errors": self.errors}


def _shape_ok(item) -> tuple[bool, str]:
    """Validate only the shape of a claimed item.

    No vendor exists yet, so there is no schema to validate against. The
    checks here are the ones that would be true for ANY vendor: an id that
    can be idempotency-keyed, and a body hash that proves a payload arrived.
    Anything else is the future vendor adapter's job.
    """
    if not item.vendor_event_id:
        return False, "missing vendor event id"
    if not item.body_sha256 or len(item.body_sha256) != 64:
        return False, "missing body hash"
    if item.body_size <= 0:
        return False, "empty payload"
    return True, ""


def process_inbox_once(inbox, *, tenant: str | None = None,
                       limit: int = 10,
                       now_iso: str | None = None) -> ProcessStats:
    """Claim up to `limit` pending items and validate their shape.

    Returns stats. Never raises on item-level failures: a bad item is marked
    held (visible, human-decidable) rather than crashing the loop.
    """
    stats = ProcessStats()
    for _ in range(limit):
        item = inbox.claim_next(tenant=tenant, now_iso=now_iso)
        if item is None:
            break
        stats = ProcessStats(claimed=stats.claimed + 1,
                             processed=stats.processed,
                             held=stats.held,
                             errors=stats.errors)
        try:
            ok, why = _shape_ok(item)
            if ok:
                inbox.mark_processed(item.inbox_id, item.tenant,
                                     now_iso or item.received_at)
                stats = ProcessStats(claimed=stats.claimed,
                                     processed=stats.processed + 1,
                                     held=stats.held,
                                     errors=stats.errors)
            else:
                inbox.mark_failed(item.inbox_id, item.tenant,
                                  now_iso or item.received_at, note=why)
                stats = ProcessStats(claimed=stats.claimed,
                                     processed=stats.processed,
                                     held=stats.held + 1,
                                     errors=stats.errors)
        except Exception:
            # DB error on mark — the item stays processing and will be
            # recovered by recover_stale later. Count it, keep going.
            stats = ProcessStats(claimed=stats.claimed,
                                 processed=stats.processed,
                                 held=stats.held,
                                 errors=stats.errors + 1)
    return stats
