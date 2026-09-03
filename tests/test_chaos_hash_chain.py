"""Owner-absent: seq-preserving splice is not a clean ledger.

Scenario 4 (duplicate delivery) already lives on the store. This file
covers the complementary hole: a middle line rewritten so seq still
looks consecutive. Timeout is not used as evidence. HALT is not a
parameter — in-flight integrity checks must still run.

Independent of ``tests/test_chaos_owner_absent.py`` (owned by an open PR).
"""

from __future__ import annotations

import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.hash_chain import (
    GENESIS,
    HashChain,
    claims_immutable,
    record_hash,
    verify_links,
)


class ScenarioSeqPreservingSpliceIsDetected(unittest.TestCase):
    def test_middle_rewrite_breaks_the_suffix(self):
        # Honest chain A → B → C. An attacker keeps seq 1,2,3 and
        # replaces body B with B-prime while leaving C's prev_hash
        # pointing at the old digest of B.
        a = record_hash(GENESIS, b"A")
        b = record_hash(a, b"B")
        c = record_hash(b, b"C")
        self.assertEqual(
            verify_links(((GENESIS, b"A"), (a, b"B"), (b, b"C"))), c)

        with self.assertRaises(FailClosedError):
            verify_links(((GENESIS, b"A"), (a, b"B-prime"), (b, b"C")))

    def test_rewritten_suffix_is_a_different_tip(self):
        # A full suffix rewrite verifies as *a* chain. It is not the
        # original tip. That is why this module never claims immutable.
        honest = HashChain()
        honest.accept(b"A")
        honest.accept(b"B")
        honest.accept(b"C")
        forged = HashChain()
        forged.accept(b"A")
        forged.accept(b"B-prime")
        forged.accept(b"C")
        self.assertNotEqual(honest.tip, forged.tip)
        self.assertFalse(claims_immutable())

    def test_identical_bodies_under_different_prev_differ(self):
        # Same payload, different predecessor → different digest.
        # Seq-alone cannot see this; the chain can.
        left = record_hash(GENESIS, b"same-body")
        right = record_hash(left, b"same-body")
        self.assertNotEqual(left, right)


class ScenarioInFlightLinkingSurvivesHaltVocabulary(unittest.TestCase):
    def test_accept_has_no_halt_switch(self):
        # Recovery without the owner still has to chain in-flight
        # appends. HALT stops STARTS, not this check.
        chain = HashChain()
        first = chain.accept(b"in-flight-1")
        second = chain.accept(b"in-flight-2", claimed_prev=first)
        self.assertEqual(len(chain), 2)
        self.assertEqual(chain.tip, second)


if __name__ == "__main__":
    unittest.main()
