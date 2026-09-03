"""Kernel-pure architecture-contract pin — complementary to artifact_ref.

A contract is cited by id + sha256 + byte_size + evidence_level.
The pin refuses an embedded body. UNKNOWN size is None, not 0.
Ready is not authorized. Distinct from artifact_ref (free path)
and from arch_bind (surface admission). Not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.arch_bind import CONTRACTS
from ofn.kernel.contract_pin import (
    EVIDENCE_LEVELS,
    ContractPin,
    agent_reported_is_verified,
    claims_immutable,
    copies_canonical,
    grants_send,
    halt_blocks_pin,
    pin_contract,
    promotes_ready_to_send,
    ready_is_authorized,
    timeout_proves_concurrent,
    unknown_is_false,
    unknown_size_is_zero,
)
from ofn.kernel.errors import FailClosedError

_DIGEST = "a" * 64


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

    def test_halt_does_not_block_pin(self):
        self.assertFalse(halt_blocks_pin())

    def test_ready_is_not_authorized(self):
        self.assertFalse(ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())

    def test_does_not_copy_canonical(self):
        self.assertFalse(copies_canonical())

    def test_unknown_size_is_not_zero(self):
        self.assertFalse(unknown_size_is_zero())

    def test_agent_reported_is_not_verified(self):
        self.assertFalse(agent_reported_is_verified())

    def test_unknown_is_not_false(self):
        self.assertFalse(unknown_is_false())

    def test_timeout_does_not_prove_concurrent(self):
        self.assertFalse(timeout_proves_concurrent())

    def test_does_not_promote_ready_to_send(self):
        self.assertFalse(promotes_ready_to_send())

    def test_signature_has_no_send_halt_or_immutable_knob(self):
        params = inspect.signature(pin_contract).parameters
        self.assertEqual(
            list(params),
            ["contract", "sha256", "byte_size", "evidence_level", "body"],
        )
        for forbidden in (
            "resend",
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "halt",
            "halt_raw",
            "immutable",
            "pointer",
        ):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            ContractPin(
                contract="task_envelope", sha256=_DIGEST, byte_size=10,
                evidence_level="B", grants_send=True)


class MintPin(unittest.TestCase):
    def test_pin_known_contract(self):
        pin = pin_contract(
            contract="task_envelope", sha256=_DIGEST, byte_size=128,
            evidence_level="B")
        self.assertEqual(pin.contract, "task_envelope")
        self.assertEqual(pin.sha256, _DIGEST)
        self.assertEqual(pin.byte_size, 128)
        self.assertEqual(pin.evidence_level, "B")
        self.assertFalse(pin.grants_send)
        self.assertFalse(pin.size_is_unknown())
        self.assertFalse(pin.independently_verified())

    def test_pin_every_known_contract(self):
        for name in CONTRACTS:
            pin = pin_contract(
                contract=name, sha256=_DIGEST, byte_size=1,
                evidence_level="A")
            self.assertEqual(pin.contract, name)
            self.assertFalse(pin.grants_send)

    def test_unknown_size_is_none_not_zero(self):
        pin = pin_contract(
            contract="receipt", sha256=_DIGEST, byte_size=None,
            evidence_level="C")
        self.assertIsNone(pin.byte_size)
        self.assertTrue(pin.size_is_unknown())
        self.assertFalse(unknown_size_is_zero())
        zero = pin_contract(
            contract="receipt", sha256=_DIGEST, byte_size=0,
            evidence_level="A")
        self.assertEqual(zero.byte_size, 0)
        self.assertFalse(zero.size_is_unknown())

    def test_evidence_levels_are_closed(self):
        self.assertEqual(EVIDENCE_LEVELS, frozenset({"A", "B", "C"}))
        for level in EVIDENCE_LEVELS:
            pin = pin_contract(
                contract="dedup", sha256=_DIGEST, byte_size=4,
                evidence_level=level)
            self.assertEqual(pin.evidence_level, level)
            self.assertFalse(pin.independently_verified())

    def test_sha256_is_folded_lowercase(self):
        pin = pin_contract(
            contract="halt", sha256="B" * 64, byte_size=2,
            evidence_level="B")
        self.assertEqual(pin.sha256, "b" * 64)

    def test_dual_record_allowed_size_and_grants_send(self):
        pin = pin_contract(
            contract="otel_map", sha256=_DIGEST, byte_size=9,
            evidence_level="B")
        self.assertTrue(hasattr(pin, "byte_size"))
        self.assertTrue(hasattr(pin, "grants_send"))
        self.assertEqual(pin.byte_size, 9)
        self.assertFalse(pin.grants_send)


class RefuseEmbedAndUnknown(unittest.TestCase):
    def test_embedded_body_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_contract(
                contract="task_envelope", sha256=_DIGEST, byte_size=3,
                evidence_level="B", body="verbatim")
        self.assertIn("embedded", str(ctx.exception).lower())
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="task_envelope", sha256=_DIGEST, byte_size=3,
                evidence_level="B", body="")

    def test_unknown_contract_is_not_classified_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_contract(
                contract="DEAD_SOURCE", sha256=_DIGEST, byte_size=1,
                evidence_level="B")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_unknown_evidence_level_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            pin_contract(
                contract="task_envelope", sha256=_DIGEST, byte_size=1,
                evidence_level="D")
        self.assertNotIn("FALSE", str(ctx.exception))

    def test_short_or_invalid_digest_fails_closed(self):
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="task_envelope", sha256="abc", byte_size=1,
                evidence_level="B")
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="task_envelope", sha256="G" * 64, byte_size=1,
                evidence_level="B")

    def test_byte_size_rejects_bool_float_str(self):
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="task_envelope", sha256=_DIGEST, byte_size=True,
                evidence_level="B")
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="task_envelope", sha256=_DIGEST, byte_size=1.0,
                evidence_level="B")
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="task_envelope", sha256=_DIGEST, byte_size="0",
                evidence_level="B")
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="task_envelope", sha256=_DIGEST, byte_size=-1,
                evidence_level="B")


class SealedNames(unittest.TestCase):
    def test_sealed_contract_fails_closed(self):
        for sealed in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
        ):
            with self.assertRaises(FailClosedError) as ctx:
                pin_contract(
                    contract=sealed, sha256=_DIGEST, byte_size=1,
                    evidence_level="B")
            self.assertIn("sealed", str(ctx.exception).lower())

    def test_ready_is_not_authorized_as_a_pin(self):
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="campaign_envelope_ready", sha256=_DIGEST,
                byte_size=1, evidence_level="B")
        with self.assertRaises(FailClosedError):
            pin_contract(
                contract="send_authorized", sha256=_DIGEST,
                byte_size=1, evidence_level="B")
        self.assertFalse(ready_is_authorized())


if __name__ == "__main__":
    unittest.main()
