import dataclasses

import pytest

pytestmark = pytest.mark.l0

from nbb_cp.kernel.errors import LedgerIntegrityError
from nbb_cp.kernel.events import (
    GENESIS_HASH,
    EventKind,
    canonical_json,
    next_event,
    verify_chain,
)


def build_chain(n: int):
    events = []
    prev = None
    for i in range(n):
        prev = next_event(prev, f"2026-01-01T00:00:{i:02d}+00:00", EventKind.PROPOSAL, {"i": i})
        events.append(prev)
    return events


class TestChain:
    def test_genesis_links_to_zero_hash(self):
        (genesis,) = build_chain(1)
        assert genesis.seq == 0
        assert genesis.prev_hash == GENESIS_HASH

    def test_chain_of_five_verifies(self):
        verify_chain(build_chain(5))

    def test_payload_tamper_detected(self):
        events = build_chain(3)
        events[1] = dataclasses.replace(events[1], payload={"i": 999})
        with pytest.raises(LedgerIntegrityError, match="forged"):
            verify_chain(events)

    def test_dropped_event_detected(self):
        events = build_chain(3)
        with pytest.raises(LedgerIntegrityError):
            verify_chain([events[0], events[2]])

    def test_reordered_events_detected(self):
        events = build_chain(3)
        with pytest.raises(LedgerIntegrityError):
            verify_chain([events[0], events[2], events[1]])

    def test_forged_prev_hash_detected(self):
        events = build_chain(2)
        events[1] = dataclasses.replace(events[1], prev_hash="f" * 64)
        with pytest.raises(LedgerIntegrityError):
            verify_chain(events)


class TestCanonicalJson:
    def test_key_order_is_stable(self):
        assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1})

    def test_unicode_preserved(self):
        assert "درآمد" in canonical_json({"note": "درآمد"})
