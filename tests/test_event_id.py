"""Kernel-pure event identity — second witness of store-minted event_id.

Independent of ``run_store.py`` (owned by an open PR). HALT stops
STARTS, not in-flight identity. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.event_id import (
    EVENT_ID_RE, EventIdIndex, grants_send, halt_blocks_event_id,
    mint_event_id, require_event_id,
)

_RAND = "a1b2c3d4e5f6a7b8"


class FactoryMintsAtTheBoundary(unittest.TestCase):
    def test_id_format_matches_store(self):
        eid = mint_event_id(_RAND)
        self.assertEqual(eid, f"evt-{_RAND}")
        self.assertTrue(EVENT_ID_RE.match(eid))
        self.assertEqual(len(_RAND), 16)

    def test_short_rand_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_event_id("short")

    def test_uppercase_hex_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_event_id("A1B2C3D4E5F6A7B8")

    def test_non_string_rand_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_event_id(16)  # type: ignore[arg-type]

    def test_bool_rand_fails_closed(self):
        with self.assertRaises(FailClosedError):
            mint_event_id(True)  # type: ignore[arg-type]


class RequireMatchesMint(unittest.TestCase):
    def test_require_accepts_minted(self):
        eid = mint_event_id(_RAND)
        self.assertEqual(require_event_id(eid), eid)

    def test_foreign_prefix_fails(self):
        with self.assertRaises(FailClosedError):
            require_event_id("run-1780000000-" + _RAND)

    def test_empty_fails(self):
        with self.assertRaises(FailClosedError):
            require_event_id("")
        with self.assertRaises(FailClosedError):
            require_event_id("   ")


class IndexRefusesCollision(unittest.TestCase):
    def test_first_record_returns_id(self):
        idx = EventIdIndex()
        eid = mint_event_id(_RAND)
        self.assertEqual(idx.record(eid), eid)
        self.assertEqual(len(idx), 1)
        self.assertTrue(idx.seen(eid))
        self.assertEqual(idx.get(eid), eid)

    def test_duplicate_id_is_collision_not_replay(self):
        idx = EventIdIndex()
        eid = mint_event_id(_RAND)
        idx.record(eid)
        with self.assertRaises(FailClosedError):
            idx.record(eid)
        self.assertEqual(len(idx), 1)

    def test_two_ids_are_two_facts(self):
        idx = EventIdIndex()
        a = mint_event_id(_RAND)
        b = mint_event_id("c" * 16)
        idx.record(a)
        idx.record(b)
        self.assertEqual(idx.replay(), (a, b))

    def test_replay_has_no_write_path(self):
        idx = EventIdIndex()
        idx.record(mint_event_id(_RAND))
        snap = idx.replay()
        self.assertEqual(len(snap), 1)
        # tuple is immutable; index length unchanged
        self.assertEqual(len(idx), 1)

    def test_get_unknown_is_none_not_false(self):
        idx = EventIdIndex()
        unknown = mint_event_id("d" * 16)
        self.assertIsNone(idx.get(unknown))
        self.assertFalse(idx.seen(unknown))


class SealedNamesAreRefused(unittest.TestCase):
    def test_rand_cannot_be_a_send_name(self):
        with self.assertRaises(FailClosedError):
            mint_event_id("send_authorized")

    def test_event_id_cannot_be_a_ready_name(self):
        with self.assertRaises(FailClosedError):
            require_event_id("campaign_envelope_ready")


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_identity(self):
        self.assertFalse(halt_blocks_event_id())
        idx = EventIdIndex()
        # recording after a would-be halt still works — no halt argument
        params = inspect.signature(idx.record).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        idx.record(mint_event_id(_RAND))
        self.assertEqual(len(idx), 1)


if __name__ == "__main__":
    unittest.main()
