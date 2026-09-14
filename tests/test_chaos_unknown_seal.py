"""Owner-absent chaos for the unknown seal.

Faults that must not flip UNKNOWN into a permission or a fact.
HALT is not a parameter. Send names stay sealed. Ready ≠ authorized.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.unknown_seal import (
    as_bool,
    classify,
    grants_send,
    halt_blocks_classify,
    ready_is_authorized,
    timeout_proves_concurrent_write,
    unknown_is_false,
)


class ChaosUnknownStaysUnknown(unittest.TestCase):
    def test_timeout_under_pressure_to_call_it_a_write(self):
        d = classify(kind="timeout", witness="lock-wait", observed="FALSE")
        self.assertEqual(d.verdict, "UNKNOWN")
        self.assertFalse(timeout_proves_concurrent_write())
        with self.assertRaises(FailClosedError):
            as_bool(d.verdict)

    def test_absent_blueprint_is_not_a_negative_finding(self):
        d = classify(kind="absent_doc", witness="MASTER-BLUEPRINT.md")
        self.assertEqual(d.verdict, "UNKNOWN")
        self.assertFalse(unknown_is_false())
        with self.assertRaises(FailClosedError):
            as_bool("UNKNOWN")

    def test_agent_report_is_not_independent_verification(self):
        d = classify(kind="agent_report_only", witness="memory-note")
        self.assertEqual(d.verdict, "UNKNOWN")
        self.assertFalse(d.grants_send)

    def test_missing_lan_port_is_not_loopback_absent(self):
        d = classify(kind="missing_port", witness="127.0.0.1:8791")
        self.assertEqual(d.verdict, "UNKNOWN")
        self.assertEqual(d.label, "inference")


class ChaosHaltAndSend(unittest.TestCase):
    def test_classify_has_no_halt_knob(self):
        self.assertNotIn("halt", inspect.signature(classify).parameters)
        self.assertFalse(halt_blocks_classify())

    def test_sealed_send_names_cannot_be_classified_as_false(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    classify(kind=name, witness="owner-absent")
                with self.assertRaises(FailClosedError):
                    classify(kind="timeout", witness=name)

    def test_ready_never_equals_authorized_after_chaos(self):
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")
        self.assertFalse(ready_is_authorized())
        self.assertFalse(grants_send())

    def test_payload_cannot_smuggle_a_send_under_halt_story(self):
        with self.assertRaises(FailClosedError):
            classify(
                kind="unparsed",
                witness="halt-flag",
                payload={"quote_sent": "held"},
            )


class ChaosCoercion(unittest.TestCase):
    def test_bool_true_cannot_bypass_classify(self):
        with self.assertRaises(FailClosedError):
            classify(
                kind="direct_observation",
                witness="chaos",
                observed=True,
            )
        with self.assertRaises(FailClosedError):
            as_bool(True)

    def test_empty_witness_cannot_mint_false(self):
        with self.assertRaises(FailClosedError):
            classify(kind="timeout", witness="")

    def test_unknown_kind_cannot_become_a_false_verdict(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify(kind="concurrent_write", witness="guess")
        self.assertIn("not FALSE", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
