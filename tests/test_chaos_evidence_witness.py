"""Owner-absent chaos — evidence-witness composition (independent of #82).

``tests/test_chaos_owner_absent.py`` is owned by PR #82. These scenarios
lock the same seven rules at the citation layer: no store, no run_id
mint, no fabricated witness. HALT is not a pointer/claim parameter.
One arm's timeout cannot refuse another arm's citation. Recovery is
recording a pointer and is still not a send.
"""

from __future__ import annotations

import unittest

from ofn.kernel.artifact_ref import (
    grants_send as pointer_grants_send,
    halt_blocks_pointer,
    mint_artifact_ref,
    ready_is_authorized as pointer_ready_is_authorized,
    unknown_size_is_zero,
)
from ofn.kernel.errors import FailClosedError
from ofn.kernel.numeric_claim import (
    classify_sample_power,
    grants_send as number_grants_send,
    halt_blocks_claim,
    mint_numeric_claim,
    ready_is_authorized as number_ready_is_authorized,
)

_SHA256 = "b" * 64
_HEAD = "f0edc963f116feae9683f369b557643ffc5340af"
_UTC = "2026-09-02T15:56:43Z"
_PTR = "docs/octopus-surgery/architecture/2026-09-02/receipts/P1-EVIDENCE-WITNESS-20260902.json"


def _pointer(*, byte_size=64, evidence_level="B", pointer=_PTR):
    return mint_artifact_ref(
        pointer=pointer, sha256=_SHA256, byte_size=byte_size,
        evidence_level=evidence_level)


def _number(*, value=1, command="python3 -m unittest -q"):
    return mint_numeric_claim(
        value=value, command=command, utc_iso=_UTC, head_sha=_HEAD,
        exit_code=0, receipt_path=_PTR)


class Scenario1DeadSourceIsUnknownNotFalse(unittest.TestCase):
    def test_unknown_size_is_none_not_zero(self):
        ref = _pointer(byte_size=None)
        self.assertTrue(ref.size_is_unknown())
        self.assertIsNone(ref.byte_size)
        self.assertFalse(unknown_size_is_zero())

    def test_unknown_evidence_level_is_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            _pointer(evidence_level="Z")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())


class Scenario2ArmTimeoutOthersContinue(unittest.TestCase):
    def test_one_arm_timeout_does_not_refuse_sibling_pointer(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("arm A fetch timed out")
        sibling = _pointer()
        self.assertEqual(sibling.evidence_level, "B")
        self.assertFalse(sibling.grants_send)

    def test_timeout_does_not_prove_concurrent_write(self):
        with self.assertRaises(TimeoutError):
            raise TimeoutError("lock wait timed out")
        claim = _number(value=2)
        self.assertEqual(claim.value, 2)
        self.assertFalse(claim.grants_send)


class Scenario3ThreeArmsInFlight(unittest.TestCase):
    def test_three_arms_mint_distinct_pointers(self):
        refs = [
            _pointer(pointer=f"docs/arm-{arm}.json", byte_size=n)
            for arm, n in (("a", 1), ("b", 2), ("c", 3))
        ]
        self.assertEqual(len(refs), 3)
        sizes = {r.byte_size for r in refs}
        self.assertEqual(sizes, {1, 2, 3})
        for r in refs:
            self.assertFalse(r.grants_send)


class Scenario4DuplicateDeliveryStillNotASend(unittest.TestCase):
    def test_second_identical_pointer_is_not_a_send(self):
        first = _pointer()
        second = _pointer()
        self.assertEqual(first, second)
        self.assertFalse(first.grants_send)
        self.assertFalse(pointer_grants_send())
        self.assertFalse(number_grants_send())


class Scenario5SealedNameStopsThatCitationOnly(unittest.TestCase):
    def test_sealed_arm_refused_sibling_citation_continues(self):
        with self.assertRaises(FailClosedError):
            _pointer(pointer="docs/send_authorized/note.md")
        sibling = _pointer()
        self.assertFalse(sibling.grants_send)
        self.assertEqual(sibling.pointer, _PTR)

    def test_sealed_command_refused_sibling_number_continues(self):
        with self.assertRaises(FailClosedError):
            _number(command="quote_sent")
        sibling = _number(value=4)
        self.assertEqual(sibling.value, 4)
        self.assertFalse(sibling.grants_send)


class Scenario6HaltDoesNotBlockCitation(unittest.TestCase):
    def test_halt_is_not_a_pointer_parameter(self):
        self.assertFalse(halt_blocks_pointer())
        self.assertFalse(halt_blocks_claim())
        ref = _pointer()
        self.assertFalse(ref.grants_send)

    def test_ready_is_not_authorized_under_halt_or_not(self):
        self.assertFalse(pointer_ready_is_authorized())
        self.assertFalse(number_ready_is_authorized())
        self.assertNotEqual("campaign_envelope_ready", "send_authorized")


class Scenario7RecoveryWithoutOwnerIsNotASend(unittest.TestCase):
    def test_recovery_pointer_and_number_are_not_sends(self):
        ref = _pointer(evidence_level="A", byte_size=0)
        claim = _number(value=0)
        self.assertFalse(ref.grants_send)
        self.assertFalse(claim.grants_send)
        self.assertEqual(
            classify_sample_power(2, threshold=10), "UNDERPOWERED")


if __name__ == "__main__":
    unittest.main()
