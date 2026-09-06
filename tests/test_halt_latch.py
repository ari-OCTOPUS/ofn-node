"""Kernel-pure HALT latch transitions (complementary P1).

The flag file is the live switch. This module locks the second
witness on main: assert/clear history, disagreement with the flag,
and no send grant. Adapter I/O lives in test_halt_log.py.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.events import FORBIDDEN_EFFECT_KINDS
from ofn.kernel.halt_latch import (
    ACTORS,
    HALT_ASSERTED,
    HALT_CLEARED,
    TRANSITION_KINDS,
    LatchIndex,
    grants_send,
    halt_blocks_latch,
    make_transition,
)

_NOW = 1780000000


def _tr(*, kind: str = HALT_ASSERTED, **overrides):
    kwargs = dict(kind=kind, now_epoch_s=_NOW, actor="owner", note=None)
    kwargs.update(overrides)
    return make_transition(**kwargs)


class FactoryVocabulary(unittest.TestCase):
    def test_kinds_are_a_closed_set(self):
        self.assertEqual(TRANSITION_KINDS, frozenset({
            HALT_ASSERTED, HALT_CLEARED,
        }))
        for name in FORBIDDEN_EFFECT_KINDS:
            self.assertNotIn(name, TRANSITION_KINDS)

    def test_actors_are_a_closed_set(self):
        self.assertEqual(ACTORS, frozenset({"owner", "supervisor"}))

    def test_record_is_not_a_run_event(self):
        rec = _tr()
        self.assertEqual(rec["kind"], HALT_ASSERTED)
        self.assertNotIn("run_id", rec)
        self.assertFalse(grants_send())

    def test_unknown_kind_refused(self):
        with self.assertRaises(FailClosedError):
            _tr(kind="HALT_MAYBE")

    def test_sealed_kind_refused(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    _tr(kind=name)

    def test_unknown_actor_refused(self):
        with self.assertRaises(FailClosedError):
            _tr(actor="script")

    def test_sealed_actor_refused(self):
        with self.assertRaises(FailClosedError):
            _tr(actor="quote_sent")

    def test_sealed_note_refused(self):
        with self.assertRaises(FailClosedError):
            _tr(note="send_authorized")

    def test_empty_note_refused(self):
        with self.assertRaises(FailClosedError):
            _tr(note="")

    def test_bool_timestamp_refused(self):
        with self.assertRaises(FailClosedError):
            _tr(now_epoch_s=True)  # type: ignore[arg-type]


class StructuralPromises(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertIs(grants_send(), False)
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_recording(self):
        self.assertIs(halt_blocks_latch(), False)


class IndexIsSecondWitness(unittest.TestCase):
    def test_assert_then_clear(self):
        idx = LatchIndex()
        self.assertFalse(idx.armed())
        self.assertEqual(idx.record(_tr()), 1)
        self.assertTrue(idx.armed())
        self.assertEqual(idx.record(_tr(kind=HALT_CLEARED, now_epoch_s=_NOW + 1)), 2)
        self.assertFalse(idx.armed())

    def test_double_assert_fails_closed(self):
        idx = LatchIndex()
        idx.record(_tr())
        with self.assertRaises(FailClosedError):
            idx.record(_tr(now_epoch_s=_NOW + 1))
        self.assertEqual(len(idx), 1)
        self.assertTrue(idx.armed())

    def test_clear_while_disarmed_fails_closed(self):
        idx = LatchIndex()
        with self.assertRaises(FailClosedError):
            idx.record(_tr(kind=HALT_CLEARED))
        self.assertEqual(len(idx), 0)
        self.assertFalse(idx.armed())

    def test_replay_is_read_only(self):
        idx = LatchIndex()
        idx.record(_tr(note="owner armed"))
        snap = idx.replay()
        self.assertEqual(len(snap), 1)
        snap[0]["note"] = "mutated"
        self.assertEqual(idx.replay()[0]["note"], "owner armed")

    def test_disagrees_with_flag_when_flag_missing(self):
        idx = LatchIndex()
        self.assertFalse(idx.disagrees_with_flag(False))
        idx.record(_tr())
        self.assertTrue(idx.disagrees_with_flag(False))
        self.assertFalse(idx.disagrees_with_flag(True))

    def test_unknown_flag_verdict_is_not_false(self):
        idx = LatchIndex()
        for bad in (None, 1, 0, "1"):
            with self.subTest(bad=bad):
                with self.assertRaises(FailClosedError):
                    idx.disagrees_with_flag(bad)

    def test_hand_built_send_kind_refused(self):
        idx = LatchIndex()
        with self.assertRaises(FailClosedError):
            idx.record({"kind": "quote_sent", "ts": _NOW,
                        "actor": "owner", "note": None})

    def test_may_record_matches_armed_state(self):
        idx = LatchIndex()
        self.assertTrue(idx.may_record(HALT_ASSERTED))
        self.assertFalse(idx.may_record(HALT_CLEARED))
        idx.record(_tr())
        self.assertFalse(idx.may_record(HALT_ASSERTED))
        self.assertTrue(idx.may_record(HALT_CLEARED))


if __name__ == "__main__":
    unittest.main()
