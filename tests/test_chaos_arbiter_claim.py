"""Owner-absent: one body's claim does not become a system-wide fact.

Independent of ``tests/test_chaos_owner_absent.py`` (owned by an open PR).
Timeout is not used as evidence. HALT is not a parameter — classifying
a claim is not a START.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.arbiter_claim import (
    classify_absence,
    classify_identity,
    grants_send,
    halt_blocks_claim,
    mint_claim,
    timeout_proves_concurrent_write,
    unknown_is_false,
)
from ofn.kernel.errors import FailClosedError


class ScenarioMissingLanPortsDoNotKillLoopback(unittest.TestCase):
    def test_lan_gap_is_unknown_with_alternatives(self):
        # A body that cannot see LAN ports must not conclude the
        # loopback APIs are gone. That is an inference with at least
        # two stories, and UNKNOWN is not FALSE.
        verdict = classify_absence("lan_ports")
        self.assertEqual(verdict, "UNKNOWN")
        self.assertFalse(unknown_is_false())
        claim = mint_claim(
            node_id="node-a",
            asserted_ip="192.0.2.10",
            claim_type="inference",
            evidence=("lan-ports-unseen",),
            alternative_explanations=(
                "loopback-listener-still-up",
                "firewall-hides-lan",
            ),
        )
        self.assertEqual(claim.scope, "this_host_only")
        self.assertFalse(claim.grants_send)


class ScenarioDiskAbsenceIsThisHostOnly(unittest.TestCase):
    def test_missing_disk_is_not_body_missing(self):
        self.assertEqual(
            classify_absence("disk_this_host"), "body_not_on_this_host")
        # Promoting that observation to system_wide without a second
        # body is refused. The body may still be on another host.
        with self.assertRaises(FailClosedError):
            mint_claim(
                node_id="node-a",
                asserted_ip="192.0.2.10",
                claim_type="measurement",
                evidence=("disk-absent-here",),
                scope="system_wide",
                peer_node_ids=("node-a",),
            )


class ScenarioTimeoutIsNotAWriter(unittest.TestCase):
    def test_timeout_does_not_prove_concurrent_write(self):
        self.assertFalse(timeout_proves_concurrent_write())
        # A measurement that the wait expired is still this_host_only.
        claim = mint_claim(
            node_id="node-a",
            asserted_ip="192.0.2.10",
            claim_type="measurement",
            evidence=("wait-expired",),
        )
        self.assertEqual(claim.scope, "this_host_only")
        self.assertFalse(grants_send())


class ScenarioIdentityContradictionStopsTheSession(unittest.TestCase):
    def test_claimed_address_mismatch_fails_closed(self):
        with self.assertRaises(FailClosedError):
            classify_identity(
                claimed_node_id="node-a",
                asserted_ip="192.0.2.10",
                observed_ip="192.0.2.180",
            )
        with self.assertRaises(FailClosedError):
            mint_claim(
                node_id="node-a",
                asserted_ip="192.0.2.10",
                claim_type="measurement",
                evidence=("eth0",),
                observed_ip="192.0.2.180",
            )


class ScenarioClassificationSurvivesHaltVocabulary(unittest.TestCase):
    def test_mint_has_no_halt_switch(self):
        self.assertNotIn("halt", inspect.signature(mint_claim).parameters)
        self.assertFalse(halt_blocks_claim())
        claim = mint_claim(
            node_id="node-a",
            asserted_ip="192.0.2.10",
            claim_type="proposal",
            evidence=("draft-only",),
        )
        self.assertEqual(claim.claim_type, "proposal")
        self.assertFalse(claim.grants_send)


if __name__ == "__main__":
    unittest.main()
