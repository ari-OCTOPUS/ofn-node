"""Kernel-pure arbiter claim — vantage, scope, and evidence pins.

Independent of ``run_store.py`` (owned by an open PR) and of
``revenue_states.py`` (owned by another). HALT is not a parameter.
Ready ≠ authorized. A typed claim is not filesystem immutability.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.arbiter_claim import (
    ArbiterClaim,
    agent_reported_is_verified,
    classify_absence,
    classify_identity,
    claims_immutable,
    grants_send,
    halt_blocks_claim,
    is_execution,
    is_independently_verified,
    mint_claim,
    promotes_ready_to_send,
    proposal_is_execution,
    require_exact_int,
    require_ipv4,
    require_node_id,
    require_two_node_ids,
    second_witness_pair,
    timeout_proves_concurrent_write,
    unknown_is_false,
)
from ofn.kernel.errors import FailClosedError


def _claim(**overrides):
    base = dict(
        node_id="node-a",
        asserted_ip="192.0.2.10",
        claim_type="measurement",
        evidence=("subject-1",),
    )
    base.update(overrides)
    return mint_claim(**base)


class StructuralPins(unittest.TestCase):
    def test_send_and_ready_pins_are_false(self):
        self.assertFalse(grants_send())
        self.assertFalse(promotes_ready_to_send())
        self.assertFalse(unknown_is_false())
        self.assertFalse(proposal_is_execution())
        self.assertFalse(agent_reported_is_verified())
        self.assertFalse(timeout_proves_concurrent_write())
        self.assertFalse(claims_immutable())
        self.assertFalse(halt_blocks_claim())

    def test_mint_signature_has_no_send_or_halt(self):
        names = set(inspect.signature(mint_claim).parameters)
        self.assertIn("scope", names)
        self.assertIn("vantage", names)
        for banned in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "resend",
            "halt",
            "halt_raw",
        ):
            self.assertNotIn(banned, names)

    def test_constructor_refuses_grants_send_true(self):
        with self.assertRaises(FailClosedError):
            ArbiterClaim(
                node_id="node-a",
                asserted_ip="192.0.2.10",
                vantage="this_host_only",
                scope="this_host_only",
                claim_type="measurement",
                evidence=("subject-1",),
                alternative_explanations=(),
                peer_node_ids=(),
                grants_send=True,
            )


class DefaultScopeIsThisHost(unittest.TestCase):
    def test_mint_defaults_to_this_host_only(self):
        claim = _claim()
        self.assertEqual(claim.scope, "this_host_only")
        self.assertEqual(claim.vantage, "this_host_only")
        self.assertFalse(claim.grants_send)
        self.assertEqual(claim.peer_node_ids, ())

    def test_this_host_only_refuses_silent_peer_list(self):
        with self.assertRaises(FailClosedError):
            _claim(peer_node_ids=("node-a", "node-b"))


class SystemWideNeedsTwoBodies(unittest.TestCase):
    def test_two_distinct_node_ids_may_name_system_wide(self):
        claim = _claim(
            scope="system_wide",
            peer_node_ids=("node-a", "node-b"),
        )
        self.assertEqual(claim.scope, "system_wide")
        self.assertEqual(set(claim.peer_node_ids), {"node-a", "node-b"})
        self.assertFalse(claim.grants_send)

    def test_one_node_id_cannot_promote(self):
        with self.assertRaises(FailClosedError):
            require_two_node_ids(("node-a",))
        with self.assertRaises(FailClosedError):
            _claim(scope="system_wide", peer_node_ids=("node-a", "node-a"))

    def test_peer_list_must_include_this_node(self):
        with self.assertRaises(FailClosedError):
            _claim(scope="system_wide", peer_node_ids=("node-b", "node-c"))

    def test_bool_is_not_a_node_id(self):
        with self.assertRaises(FailClosedError):
            require_node_id(True)
        with self.assertRaises(FailClosedError):
            require_two_node_ids((True, False))


class SealedNamesRefuse(unittest.TestCase):
    def test_sealed_claim_type_refused(self):
        for name in (
            "send_authorized",
            "quote_sent",
            "campaign_envelope_ready",
            "send-authorized",
        ):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    _claim(claim_type=name)

    def test_sealed_node_id_refused(self):
        with self.assertRaises(FailClosedError):
            require_node_id("send_authorized")

    def test_empty_evidence_is_self_confirming(self):
        with self.assertRaises(FailClosedError):
            _claim(evidence=())


class ExactIntAndAddress(unittest.TestCase):
    def test_true_is_not_one(self):
        with self.assertRaises(FailClosedError):
            require_exact_int(True, what="count")
        with self.assertRaises(FailClosedError):
            require_exact_int(1.0, what="count")
        with self.assertRaises(FailClosedError):
            require_exact_int("1", what="count")
        self.assertEqual(require_exact_int(1, what="count"), 1)

    def test_unspecified_address_refused(self):
        with self.assertRaises(FailClosedError):
            require_ipv4("0.0.0.0")

    def test_leading_zero_octet_refused(self):
        with self.assertRaises(FailClosedError):
            require_ipv4("192.168.001.1")

    def test_valid_documentation_address_accepted(self):
        self.assertEqual(require_ipv4("192.0.2.10"), "192.0.2.10")


class AbsenceAndIdentity(unittest.TestCase):
    def test_disk_this_host_is_not_body_missing(self):
        self.assertEqual(classify_absence("disk_this_host"), "body_not_on_this_host")
        self.assertNotEqual(classify_absence("disk_this_host"), "body_missing")

    def test_missing_lan_ports_are_unknown_not_loopback_absent(self):
        self.assertEqual(classify_absence("lan_ports"), "UNKNOWN")
        self.assertNotEqual(classify_absence("lan_ports"), "loopback_absent")

    def test_unknown_absence_kind_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_absence("body_missing")

    def test_missing_observed_ip_is_unknown_not_false(self):
        self.assertEqual(
            classify_identity(
                claimed_node_id="node-a",
                asserted_ip="192.0.2.10",
                observed_ip=None,
            ),
            "UNKNOWN",
        )
        self.assertFalse(unknown_is_false())

    def test_identity_contradiction_fails_closed(self):
        with self.assertRaises(FailClosedError) as ctx:
            classify_identity(
                claimed_node_id="node-a",
                asserted_ip="192.0.2.10",
                observed_ip="192.0.2.99",
            )
        self.assertIn("identity_contradiction", str(ctx.exception))

    def test_matching_observed_ip_is_consistent(self):
        self.assertEqual(
            classify_identity(
                claimed_node_id="node-a",
                asserted_ip="192.0.2.10",
                observed_ip="192.0.2.10",
            ),
            "consistent",
        )

    def test_mint_refuses_contradiction(self):
        with self.assertRaises(FailClosedError):
            _claim(observed_ip="192.0.2.99")


class ClaimTypesAreNotEffects(unittest.TestCase):
    def test_no_claim_type_is_execution(self):
        for kind in ("measurement", "inference", "proposal", "agent_reported"):
            with self.subTest(kind=kind):
                self.assertFalse(is_execution(kind))
                self.assertFalse(is_independently_verified(kind))

    def test_inference_needs_two_alternatives(self):
        with self.assertRaises(FailClosedError):
            _claim(claim_type="inference")
        with self.assertRaises(FailClosedError):
            _claim(
                claim_type="inference",
                alternative_explanations=("only-one",),
            )
        claim = _claim(
            claim_type="inference",
            alternative_explanations=("loopback-still-up", "listener-down"),
        )
        self.assertEqual(claim.claim_type, "inference")
        self.assertFalse(is_execution(claim.claim_type))


class SecondWitness(unittest.TestCase):
    def test_two_measurements_from_two_nodes_pair(self):
        a = _claim(evidence=("subject-1", "note-a"))
        b = mint_claim(
            node_id="node-b",
            asserted_ip="192.0.2.11",
            claim_type="measurement",
            evidence=("subject-1",),
        )
        self.assertTrue(second_witness_pair(a, b, subject="subject-1"))
        self.assertFalse(grants_send())

    def test_same_body_cannot_pair(self):
        a = _claim()
        b = _claim(evidence=("subject-1", "other"))
        with self.assertRaises(FailClosedError):
            second_witness_pair(a, b, subject="subject-1")

    def test_two_agent_reports_are_not_verified(self):
        a = _claim(claim_type="agent_reported")
        b = mint_claim(
            node_id="node-b",
            asserted_ip="192.0.2.11",
            claim_type="agent_reported",
            evidence=("subject-1",),
        )
        self.assertFalse(second_witness_pair(a, b, subject="subject-1"))
        self.assertFalse(agent_reported_is_verified())


if __name__ == "__main__":
    unittest.main()
