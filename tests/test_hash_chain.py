"""Kernel-pure prev_hash chain — second witness of append-only integrity.

Independent of ``run_store.py`` (owned by an open PR) and of ``seq.py``
(owned by another). HALT stops STARTS, not in-flight linking.
Ready ≠ authorized. A passing chain is not filesystem immutability.
"""

from __future__ import annotations

import inspect
import unittest

from ofn.kernel.errors import FailClosedError
from ofn.kernel.hash_chain import (
    GENESIS,
    HashChain,
    claims_immutable,
    grants_send,
    halt_blocks_chain,
    record_hash,
    refuse_sealed_chain_label,
    require_hex,
    verify_links,
)


class GenesisAndFirstLink(unittest.TestCase):
    def test_empty_chain_tips_at_genesis(self):
        chain = HashChain()
        self.assertEqual(chain.tip, GENESIS)
        self.assertEqual(len(chain), 0)
        self.assertEqual(len(GENESIS), 64)
        self.assertTrue(chain.peek_would_accept(b"first"))
        self.assertFalse(chain.peek_would_accept(b""))

    def test_first_accept_moves_tip(self):
        chain = HashChain()
        digest = chain.accept(b"first")
        self.assertEqual(digest, record_hash(GENESIS, b"first"))
        self.assertEqual(chain.tip, digest)
        self.assertEqual(chain.replay(), (digest,))
        self.assertNotEqual(digest, GENESIS)


class PrevMustMatchTip(unittest.TestCase):
    def test_wrong_claimed_prev_refused_and_chain_unchanged(self):
        chain = HashChain()
        first = chain.accept(b"A")
        other = record_hash(GENESIS, b"not-A")
        with self.assertRaises(FailClosedError):
            chain.accept(b"B", claimed_prev=other)
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain.tip, first)

    def test_honest_claimed_prev_accepted(self):
        chain = HashChain()
        first = chain.accept(b"A", claimed_prev=GENESIS)
        second = chain.accept(b"B", claimed_prev=first)
        self.assertEqual(chain.replay(), (first, second))
        self.assertEqual(chain.tip, second)


class MalformedInputFailsClosed(unittest.TestCase):
    def test_empty_body_refused(self):
        chain = HashChain()
        with self.assertRaises(FailClosedError):
            chain.accept(b"")
        self.assertEqual(len(chain), 0)

    def test_bool_is_not_bytes(self):
        chain = HashChain()
        with self.assertRaises(FailClosedError):
            chain.accept(True)  # type: ignore[arg-type]
        with self.assertRaises(FailClosedError):
            record_hash(GENESIS, False)  # type: ignore[arg-type]

    def test_string_body_refused(self):
        chain = HashChain()
        with self.assertRaises(FailClosedError):
            chain.accept("first")  # type: ignore[arg-type]

    def test_uppercase_hex_refused(self):
        # All-zero GENESIS has no letters; use a digest that actually
        # changes case so the pin is the alphabet, not the digits.
        mixed = record_hash(GENESIS, b"case-pin")
        self.assertNotEqual(mixed, mixed.upper())
        with self.assertRaises(FailClosedError):
            require_hex(mixed.upper(), what="digest")

    def test_short_digest_refused(self):
        with self.assertRaises(FailClosedError):
            require_hex("abc", what="digest")

    def test_none_digest_refused(self):
        with self.assertRaises(FailClosedError):
            require_hex(None, what="digest")


class PeekDoesNotWrite(unittest.TestCase):
    def test_peek_true_does_not_advance(self):
        chain = HashChain()
        self.assertTrue(chain.peek_would_accept(b"A"))
        self.assertEqual(chain.tip, GENESIS)
        self.assertEqual(len(chain), 0)

    def test_peek_invalid_is_false_not_raise(self):
        chain = HashChain()
        self.assertFalse(chain.peek_would_accept(True))  # type: ignore[arg-type]
        self.assertFalse(chain.peek_would_accept(b""))
        self.assertFalse(chain.peek_would_accept("A"))  # type: ignore[arg-type]
        self.assertFalse(
            chain.peek_would_accept(b"A", claimed_prev="not-hex"))


class VerifyLinksIsReadOnly(unittest.TestCase):
    def test_empty_walk_returns_genesis(self):
        self.assertEqual(verify_links(()), GENESIS)
        self.assertEqual(verify_links([]), GENESIS)

    def test_honest_three_links(self):
        a = record_hash(GENESIS, b"A")
        b = record_hash(a, b"B")
        c = record_hash(b, b"C")
        self.assertEqual(verify_links(((GENESIS, b"A"), (a, b"B"), (b, b"C"))), c)

    def test_first_link_must_cite_genesis(self):
        other = record_hash(GENESIS, b"other")
        with self.assertRaises(FailClosedError):
            verify_links(((other, b"A"),))


class SealedLabelIsNotALink(unittest.TestCase):
    def test_send_name_refused_as_label(self):
        for name in ("send_authorized", "quote_sent", "campaign_envelope_ready"):
            with self.subTest(name=name):
                with self.assertRaises(FailClosedError):
                    refuse_sealed_chain_label(name)


class ReadyIsNotAuthorized(unittest.TestCase):
    def test_grants_send_is_structurally_false(self):
        self.assertFalse(grants_send())
        self.assertEqual(list(inspect.signature(grants_send).parameters), [])

    def test_halt_does_not_block_chain(self):
        self.assertFalse(halt_blocks_chain())
        params = inspect.signature(HashChain.accept).parameters
        self.assertNotIn("halted", params)
        self.assertNotIn("halt", params)
        chain = HashChain()
        chain.accept(b"in-flight")
        self.assertEqual(len(chain), 1)

    def test_does_not_claim_immutable(self):
        self.assertFalse(claims_immutable())
        self.assertEqual(list(inspect.signature(claims_immutable).parameters), [])


if __name__ == "__main__":
    unittest.main()
