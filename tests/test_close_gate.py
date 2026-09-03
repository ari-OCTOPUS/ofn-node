"""Kernel-pure close gate — second witness of append-after-close.

Independent of ``run_store.py`` (owned by an open PR). HALT stops
STARTS, not in-flight close. A causal ref still closes. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.close_gate import CloseGate, grants_send, halt_blocks_close
from ofn.kernel.errors import FailClosedError

_RUN_A = "run-1780000000-a1b2c3d4e5f6a7b8"
_RUN_B = "run-1780000000-b1b2c3d4e5f6a7b8"
_REF = "evt-aaaaaaaaaaaaaaaa"


class OpenThenClose(unittest.TestCase):
    def test_open_may_append_then_close_refuses(self):
        gate = CloseGate()
        self.assertTrue(gate.note_open(_RUN_A))
        self.assertTrue(gate.may_append(_RUN_A))
        gate.refuse_append(_RUN_A)
        gate.note_closed(_RUN_A)
        self.assertTrue(gate.is_closed(_RUN_A))
        self.assertFalse(gate.may_append(_RUN_A))
        with self.assertRaises(FailClosedError) as ctx:
            gate.refuse_append(_RUN_A)
        self.assertIn("append_after_close", str(ctx.exception))

    def test_close_with_causal_ref_still_closes(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        gate.note_closed(_RUN_A, ref=_REF)
        self.assertTrue(gate.is_closed(_RUN_A))
        with self.assertRaises(FailClosedError):
            gate.refuse_append(_RUN_A)

    def test_second_close_is_append_after_close(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        gate.note_closed(_RUN_A, ref=_REF)
        with self.assertRaises(FailClosedError):
            gate.note_closed(_RUN_A)
        self.assertEqual(gate.replay(), ((_RUN_A, True),))

    def test_reopen_same_id_refused(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        gate.note_closed(_RUN_A)
        with self.assertRaises(FailClosedError) as ctx:
            gate.note_open(_RUN_A)
        self.assertIn("new run_id", str(ctx.exception))

    def test_re_note_open_is_idempotent(self):
        gate = CloseGate()
        self.assertTrue(gate.note_open(_RUN_A))
        self.assertFalse(gate.note_open(_RUN_A))
        self.assertEqual(len(gate), 1)
        self.assertTrue(gate.may_append(_RUN_A))


class UnknownAndSealed(unittest.TestCase):
    def test_close_unknown_run_refused(self):
        gate = CloseGate()
        with self.assertRaises(FailClosedError):
            gate.note_closed(_RUN_A)
        self.assertFalse(gate.known(_RUN_A))
        self.assertFalse(gate.is_closed(_RUN_A))

    def test_append_unknown_run_refused(self):
        gate = CloseGate()
        self.assertFalse(gate.may_append(_RUN_A))
        with self.assertRaises(FailClosedError) as ctx:
            gate.refuse_append(_RUN_A)
        self.assertIn("unknown run", str(ctx.exception))

    def test_sealed_run_id_refused(self):
        gate = CloseGate()
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    gate.note_open(name)

    def test_sealed_ref_on_close_refused_and_run_stays_open(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        with self.assertRaises(FailClosedError):
            gate.note_closed(_RUN_A, ref="send_authorized")
        self.assertFalse(gate.is_closed(_RUN_A))
        gate.refuse_append(_RUN_A)

    def test_malformed_run_id_refused(self):
        gate = CloseGate()
        with self.assertRaises(FailClosedError):
            gate.note_open("run-1-short")
        self.assertEqual(len(gate), 0)


class SiblingArmsContinue(unittest.TestCase):
    def test_closing_one_run_does_not_close_another(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        gate.note_open(_RUN_B)
        gate.note_closed(_RUN_A, ref=_REF)
        with self.assertRaises(FailClosedError):
            gate.refuse_append(_RUN_A)
        gate.refuse_append(_RUN_B)
        self.assertTrue(gate.may_append(_RUN_B))
        self.assertEqual(gate.replay(), ((_RUN_A, True), (_RUN_B, False)))

    def test_recovery_is_a_new_run_id(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        gate.note_closed(_RUN_A)
        self.assertTrue(gate.note_open(_RUN_B))
        gate.refuse_append(_RUN_B)
        self.assertNotEqual(_RUN_A, _RUN_B)


class PeekDoesNotWrite(unittest.TestCase):
    def test_may_append_does_not_close(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        self.assertTrue(gate.may_append(_RUN_A))
        self.assertFalse(gate.is_closed(_RUN_A))
        self.assertEqual(len(gate), 1)

    def test_replay_is_a_tuple(self):
        gate = CloseGate()
        gate.note_open(_RUN_A)
        snap = gate.replay()
        self.assertIsInstance(snap, tuple)
        self.assertEqual(snap, ((_RUN_A, False),))


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_close(self):
        self.assertFalse(halt_blocks_close())
        params = inspect.signature(CloseGate.note_closed).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        gate = CloseGate()
        gate.note_open(_RUN_A)
        gate.note_closed(_RUN_A)
        self.assertTrue(gate.is_closed(_RUN_A))

    def test_no_resend_or_send_authorized_parameter(self):
        for fn in (CloseGate.note_open, CloseGate.note_closed,
                   CloseGate.refuse_append, CloseGate.may_append):
            names = list(inspect.signature(fn).parameters)
            self.assertNotIn("resend", names)
            self.assertNotIn("send_authorized", names)


if __name__ == "__main__":
    unittest.main()
