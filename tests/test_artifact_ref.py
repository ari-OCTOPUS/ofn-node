"""Kernel-pure artifact pointer — complementary to receipts and incidents.

A pointer cites a body by path + sha256 + byte size + evidence level.
It does not embed the document. HALT is not a parameter. Ready is not
authorized. This module is not wired into the run store.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.artifact_ref import (
    EVIDENCE_LEVELS,
    ArtifactRef,
    agent_reported_is_verified,
    claims_immutable,
    copies_canonical,
    grants_send,
    halt_blocks_pointer,
    mint_artifact_ref,
    ready_is_authorized,
    require_byte_size,
    require_rel_path,
    require_sha256,
    unknown_size_is_zero,
)
from ofn.kernel.errors import FailClosedError

_SHA = "a" * 64
_PTR = "docs/octopus-surgery/architecture/2026-09-02/receipts/P1-EVIDENCE-WITNESS-20260902.json"


def _ref(**overrides):
    kwargs = dict(
        pointer=_PTR, sha256=_SHA, byte_size=128, evidence_level="B",
    )
    kwargs.update(overrides)
    return mint_artifact_ref(**kwargs)


class StructuralPins(unittest.TestCase):
    def test_grants_send_is_false(self):
        self.assertFalse(grants_send())

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

    def test_halt_does_not_block_pointers(self):
        self.assertFalse(halt_blocks_pointer())

    def test_signature_has_no_send_halt_or_resend_knob(self):
        params = inspect.signature(mint_artifact_ref).parameters
        self.assertEqual(
            list(params),
            ["pointer", "sha256", "byte_size", "evidence_level", "body"],
        )
        for forbidden in ("resend", "send_authorized", "quote_sent",
                          "campaign_envelope_ready", "halt", "halt_raw",
                          "immutable"):
            self.assertNotIn(forbidden, params)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            ArtifactRef(pointer=_PTR, sha256=_SHA, byte_size=1,
                        evidence_level="B", grants_send=True)

    def test_closed_evidence_levels(self):
        self.assertEqual(EVIDENCE_LEVELS, frozenset({"A", "B", "C"}))


class PointerValidation(unittest.TestCase):
    def test_absolute_path_refused(self):
        with self.assertRaises(FailClosedError):
            _ref(pointer="/etc/passwd")

    def test_parent_traversal_refused(self):
        with self.assertRaises(FailClosedError):
            _ref(pointer="docs/../secrets.env")

    def test_backslash_refused(self):
        with self.assertRaises(FailClosedError):
            require_rel_path(r"docs\foo.md")

    def test_empty_path_refused(self):
        with self.assertRaises(FailClosedError):
            _ref(pointer="   ")

    def test_bool_path_refused(self):
        with self.assertRaises(FailClosedError):
            require_rel_path(True)

    def test_sealed_path_component_refused(self):
        for name in ("send_authorized", "quote_sent",
                     "campaign_envelope_ready", "send-authorized"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    _ref(pointer=f"docs/{name}/note.md")
                with self.assertRaises(FailClosedError):
                    _ref(pointer=name)


class DigestAndSize(unittest.TestCase):
    def test_short_digest_refused(self):
        with self.assertRaises(FailClosedError):
            require_sha256("abc")
        with self.assertRaises(FailClosedError):
            _ref(sha256="a" * 7)

    def test_uppercase_digest_accepted_folded(self):
        ref = _ref(sha256="A" * 64)
        self.assertEqual(ref.sha256, "a" * 64)

    def test_none_size_is_unknown_not_zero(self):
        ref = _ref(byte_size=None)
        self.assertTrue(ref.size_is_unknown())
        self.assertIsNone(ref.byte_size)
        self.assertNotEqual(ref.byte_size, 0)

    def test_zero_size_is_a_measurement(self):
        ref = _ref(byte_size=0)
        self.assertFalse(ref.size_is_unknown())
        self.assertEqual(ref.byte_size, 0)

    def test_negative_size_refused(self):
        with self.assertRaises(FailClosedError):
            require_byte_size(-1)

    def test_bool_size_refused(self):
        with self.assertRaises(FailClosedError):
            require_byte_size(True)
        with self.assertRaises(FailClosedError):
            _ref(byte_size=True)

    def test_float_size_refused(self):
        with self.assertRaises(FailClosedError):
            require_byte_size(1.0)

    def test_string_size_refused(self):
        with self.assertRaises(FailClosedError):
            require_byte_size("128")


class EvidenceLevelAndBody(unittest.TestCase):
    def test_unknown_level_fails_closed_not_false(self):
        with self.assertRaises(FailClosedError) as ctx:
            _ref(evidence_level="D")
        self.assertNotIn("FALSE", str(ctx.exception))
        self.assertIn("unknown", str(ctx.exception).lower())

    def test_empty_level_refused(self):
        with self.assertRaises(FailClosedError):
            _ref(evidence_level="")

    def test_sealed_level_refused(self):
        with self.assertRaises(FailClosedError):
            _ref(evidence_level="send_authorized")

    def test_embedded_body_refused_even_when_empty(self):
        with self.assertRaises(FailClosedError):
            mint_artifact_ref(
                pointer=_PTR, sha256=_SHA, byte_size=0,
                evidence_level="B", body="")
        with self.assertRaises(FailClosedError):
            mint_artifact_ref(
                pointer=_PTR, sha256=_SHA, byte_size=4,
                evidence_level="B", body="title: copied")

    def test_absent_body_mints(self):
        ref = _ref()
        self.assertEqual(ref.pointer, _PTR)
        self.assertEqual(ref.byte_size, 128)
        self.assertEqual(ref.evidence_level, "B")
        self.assertFalse(ref.grants_send)
        self.assertFalse(ref.independently_verified())

    def test_level_c_is_not_independently_verified(self):
        ref = _ref(evidence_level="C")
        self.assertFalse(ref.independently_verified())
        self.assertFalse(agent_reported_is_verified())

    def test_level_a_is_still_one_record(self):
        ref = _ref(evidence_level="A")
        self.assertFalse(ref.independently_verified())


if __name__ == "__main__":
    unittest.main()
